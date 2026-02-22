"""
DocuForge AI — Analysis Routes

HTTP endpoints for document analysis operations. Routes delegate to
services and workers for actual processing.
"""

import logging
from pathlib import Path
from uuid import uuid4

from celery.result import AsyncResult
from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from api.workers.celery_app import celery_app
from api.workers.analysis_tasks import run_analysis_pipeline
from core.eval.eval_queries import compute_eval_trend, fetch_eval_history
from core.memory.long_term import get_session_by_id
from core.rag.vector_queries import list_all_collections

logger = logging.getLogger(__name__)

router = APIRouter()

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

# Allowed file extensions
ALLOWED_EXTENSIONS = {"pdf", "png", "jpg", "jpeg", "mp3", "wav", "xlsx", "pptx"}


@router.post("/analyze")
async def analyze_document(
    file: UploadFile = File(...),
    query: str = Form(...),
    prompt_version: str = Form(default="v3"),
) -> dict:
    """
    Accept a document file and a query, save the file, and dispatch an async
    analysis task to Celery. Returns immediately with task ID and status.
    
    Args:
        file: Uploaded document file
        query: User query for analysis
        
    Returns:
        Task ID, status, and session ID for status polling
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")

    if not query or not query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    # Validate file extension
    file_ext = Path(file.filename).suffix.lower().lstrip(".")
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: .{file_ext}. "
                   f"Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
        )

    try:
        # Generate unique filename preserving extension
        unique_filename = f"{uuid4()}{Path(file.filename).suffix}"
        file_path = UPLOAD_DIR / unique_filename

        # Save file
        contents = await file.read()
        with open(file_path, "wb") as f:
            f.write(contents)

        logger.info(
            "Uploaded file: %s → %s (%d bytes)",
            file.filename,
            unique_filename,
            len(contents)
        )

        # Generate session ID and dispatch task
        session_id = str(uuid4())
        task = run_analysis_pipeline.delay(str(file_path), query, session_id, prompt_version)

        logger.info(
            "Dispatched analysis task: task_id=%s, session_id=%s",
            task.id,
            session_id
        )

        return {
            "task_id": task.id,
            "status": "queued",
            "session_id": session_id,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error("File upload failed: %s", str(e))
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@router.get("/status/{task_id}")
async def check_task_status(task_id: str) -> dict:
    """
    Check the status of an async analysis task. Returns task status and result
    if available, or null if still processing.
    
    Args:
        task_id: Celery task identifier
        
    Returns:
        Task status and result (if available)
    """
    task_result = AsyncResult(task_id, app=celery_app)

    # Map Celery states to friendly API responses
    status_map = {
        "PENDING": "queued",
        "STARTED": "started",
        "SUCCESS": "success",
        "FAILURE": "failure",
    }

    friendly_status = status_map.get(task_result.state, "processing")

    response = {
        "task_id": task_id,
        "status": friendly_status,
    }

    if task_result.state == "SUCCESS":
        response["result"] = task_result.result
    elif task_result.state == "FAILURE":
        response["result"] = {"error": str(task_result.result)}

    logger.debug(
        "Task status check: task_id=%s, state=%s, friendly_status=%s",
        task_id,
        task_result.state,
        friendly_status
    )
    
    return response


@router.get("/sessions/{session_id}")
async def get_session(session_id: str) -> dict:
    """
    Fetch a session by session_id from long-term memory. Returns the full
    session record or 404 if not found.
    """
    session = get_session_by_id(session_id)
    
    if session is None:
        logger.warning("Session not found: session_id=%s", session_id)
        raise HTTPException(status_code=404, detail="Session not found")
    
    logger.info("Session retrieved: session_id=%s", session_id)
    return session


@router.get("/sessions/{session_id}/trace")
async def get_session_trace(session_id: str) -> list:
    """
    Fetch the agent execution trace for a session. Returns the agent_trace list
    as a JSON array or empty array if session not found.
    """
    session = get_session_by_id(session_id)
    
    if session is None:
        logger.warning("Session not found for trace: session_id=%s", session_id)
        raise HTTPException(status_code=404, detail="Session not found")
    
    import json
    agent_trace = session.get("agent_trace_json", "[]")
    
    try:
        trace_list = json.loads(agent_trace) if isinstance(agent_trace, str) else agent_trace
    except Exception as e:
        logger.warning("Failed to parse agent trace: %s", str(e))
        trace_list = []
    
    logger.debug("Session trace retrieved: session_id=%s, entries=%d", session_id, len(trace_list))
    return trace_list


@router.post("/eval/run")
async def run_evaluation(request_data: dict | None = None) -> dict:
    """
    Dispatch a Celery task to run accuracy evaluation. Accepts optional 'subset'
    field with list of eval IDs to run. Returns task_id and status.
    """
    if request_data is None:
        request_data = {}
    
    subset = request_data.get("subset", [])
    
    try:
        task = celery_app.send_task(
            "api.workers.evaluation_tasks.run_accuracy_evaluation",
            args=[subset],
        )
        
        logger.info("Dispatched evaluation task: %s (subset size: %d)", task.id, len(subset))
        
        return {
            "task_id": task.id,
            "status": "queued",
        }
    except Exception as e:
        logger.error("Failed to dispatch evaluation task: %s", str(e))
        raise HTTPException(status_code=500, detail=f"Evaluation dispatch failed: {str(e)}")


@router.get("/eval/history")
async def get_eval_history(limit: int = 50) -> dict:
    """
    Fetch recent evaluation results from the database.
    Returns list of results with accuracy/faithfulness scores, timestamps.
    """
    results = fetch_eval_history(limit=limit)
    
    logger.debug("Eval history retrieved: %d results", len(results))
    return {
        "total": len(results),
        "results": results,
    }


@router.get("/eval/trend")
async def get_eval_trend(days: int = 30) -> dict:
    """
    Compute daily aggregated evaluation metrics over the past N days.
    Returns dates, accuracy_scores, and faithfulness_scores as arrays.
    """
    trend = compute_eval_trend(days=days)
    
    logger.debug("Eval trend computed: %d days", len(trend.get("dates", [])))
    return trend


@router.get("/collections")
async def list_collections() -> dict:
    """
    List all ChromaDB vector store collections.
    Returns collection names and metadata.
    """
    try:
        import chromadb

        client = chromadb.Client()
        collections = list_all_collections(client)
        
        logger.debug("Collections retrieved: %d total", len(collections))
        return {
            "total": len(collections),
            "collections": collections,
        }
    except Exception as e:
        logger.warning("Failed to list collections: %s", str(e))
        return {
            "total": 0,
            "collections": [],
        }


@router.get("/prompts")
async def get_prompts() -> dict:
    """
    Fetch all available prompt versions (v1, v2, v3) for the writer agent.
    Returns prompt content with metadata and active version indicator.
    """
    
    prompts_dir = Path("prompts")
    prompts = {}
    
    for version in ["v1", "v2", "v3"]:
        try:
            prompt_file = prompts_dir / version / "writer_prompt.txt"
            if prompt_file.exists():
                with open(prompt_file, "r", encoding="utf-8") as f:
                    content = f.read()
                prompts[version] = {
                    "content": content,
                    "active": version == "v3",  # v3 is the active version
                    "version": version,
                }
            else:
                logger.warning("Prompt file not found: %s", prompt_file)
                prompts[version] = {
                    "content": f"(Prompt file not found for {version})",
                    "active": version == "v3",
                    "version": version,
                }
        except Exception as e:
            logger.warning("Failed to read prompt %s: %s", version, str(e))
            prompts[version] = {
                "content": f"(Error reading {version}: {str(e)})",
                "active": version == "v3",
                "version": version,
            }
    
    logger.debug("Prompts retrieved: %d versions", len(prompts))
    return {
        "total": len(prompts),
        "prompts": prompts,
    }
