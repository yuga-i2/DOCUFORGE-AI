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

logger = logging.getLogger(__name__)

router = APIRouter()

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


@router.post("/analyze")
async def analyze_document(
    file: UploadFile = File(...),
    query: str = Form(...),
) -> dict:
    """
    Accept a document file and a query, save the file, and dispatch an async
    analysis task to Celery. Returns immediately with task ID and status.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")

    if not query or not query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    try:
        # Generate unique filename preserving extension
        file_ext = Path(file.filename).suffix
        unique_filename = f"{uuid4()}{file_ext}"
        file_path = UPLOAD_DIR / unique_filename

        # Save file
        with open(file_path, "wb") as f:
            contents = await file.read()
            f.write(contents)

        logger.info("Uploaded file: %s → %s (%d bytes)", file.filename, unique_filename, len(contents))

        # Generate session ID and dispatch task
        session_id = str(uuid4())
        task = celery_app.send_task(
            "api.workers.analysis_tasks.run_analysis_pipeline",
            args=[str(file_path), query, session_id],
        )

        logger.info("Dispatched analysis task: %s (session: %s)", task.id, session_id)

        return {
            "task_id": task.id,
            "status": "queued",
            "session_id": session_id,
        }
    except Exception as e:
        logger.error("File upload failed: %s", str(e))
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@router.get("/status/{task_id}")
async def check_task_status(task_id: str) -> dict:
    """
    Check the status of an async analysis task. Returns task status and result
    if available, or null if still processing.
    """
    result = AsyncResult(task_id, app=celery_app)

    response = {
        "task_id": task_id,
        "status": result.state,
    }

    if result.state == "SUCCESS":
        response["result"] = result.result
    elif result.state == "FAILURE":
        response["error"] = str(result.result)

    logger.debug("Task status check: %s → %s", task_id, result.state)
    return response
