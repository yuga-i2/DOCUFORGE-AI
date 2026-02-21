"""
DocuForge AI — FastAPI Application Entry Point

Initialises the FastAPI application, registers routers, and configures
middleware. All business logic lives in services — this file only wires
the HTTP layer together.
"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes.analysis_router import router as analysis_router

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle application startup and shutdown events."""
    logger.info("DocuForge AI starting up")
    yield
    logger.info("DocuForge AI shutting down")


app = FastAPI(
    title="DocuForge AI",
    description="Multi-agent document intelligence platform",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(analysis_router, prefix="/api/v1", tags=["analysis"])


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Return service health status."""
    return {"status": "healthy", "service": "docuforge-ai"}
