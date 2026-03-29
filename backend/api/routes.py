import uuid
import os
from pathlib import Path
from typing import Optional

import aiofiles
from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks
from sse_starlette.sse import EventSourceResponse

from api.schemas import (
    UploadResponse,
    StartReviewRequest,
    StartReviewResponse,
    ReviewStatus,
    ReviewReport,
)
from services.sse_service import SSEService
from services.review_service import get_review_service

router = APIRouter()

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

# In-memory session store (replace with Redis/DB in production)
sessions: dict[str, dict] = {}


@router.post("/review/upload", response_model=UploadResponse)
async def upload_prd(file: UploadFile = File(...)):
    """Upload PRD document for review."""
    if file.size and file.size > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large (max 10MB)")

    session_id = str(uuid.uuid4())
    filename = file.filename or "unknown"
    suffix = Path(filename).suffix.lower()

    if suffix not in [".md", ".docx"]:
        raise HTTPException(status_code=400, detail="Unsupported file type")

    file_type = "markdown" if suffix == ".md" else "docx"
    file_path = UPLOAD_DIR / f"{session_id}{suffix}"

    async with aiofiles.open(file_path, "wb") as f:
        content = await file.read()
        await f.write(content)

    # Create SSE service here so it can be shared
    sse_service = SSEService(session_id)

    sessions[session_id] = {
        "filename": filename,
        "file_type": file_type,
        "size": len(content),
        "file_path": str(file_path),
        "status": "uploaded",
        "preset": "normal",
        "sse_service": sse_service,
    }

    return UploadResponse(
        session_id=session_id,
        filename=filename,
        file_type=file_type,
        size=len(content),
    )


async def run_review(session_id: str, file_path: str, preset: str, sse_service: SSEService):
    """Background task to run the review."""
    try:
        review_service = get_review_service(
            session_id=session_id,
            file_path=file_path,
            preset=preset,
            sse_service=sse_service,
        )
        result = await review_service.start()

        # Update session with completed status
        if session_id in sessions:
            sessions[session_id]["status"] = "completed"
            sessions[session_id]["report"] = result.get("report", {})
    except Exception as e:
        if session_id in sessions:
            sessions[session_id]["status"] = "error"
            sessions[session_id]["error"] = str(e)


@router.post("/review/start", response_model=StartReviewResponse)
async def start_review(request: StartReviewRequest, background_tasks: BackgroundTasks):
    """Start PRD review process."""
    session_id = request.session_id

    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    session = sessions[session_id]
    session["status"] = "started"
    session["preset"] = request.preset.value

    # Start review in background with shared SSE service
    background_tasks.add_task(
        run_review,
        session_id,
        session["file_path"],
        request.preset.value,
        session["sse_service"],
    )

    return StartReviewResponse(status="started", session_id=session_id)


@router.get("/review/stream/{session_id}")
async def stream_review(session_id: str):
    """SSE endpoint for streaming review progress."""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    sse_service = sessions[session_id]["sse_service"]

    return EventSourceResponse(sse_service.event_generator())


@router.get("/review/status/{session_id}", response_model=ReviewStatus)
async def get_review_status(session_id: str):
    """Get current review status."""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    session = sessions[session_id]
    return ReviewStatus(
        session_id=session_id,
        status=session.get("status", "unknown"),
        current_dimension=session.get("current_dimension"),
        completed_dimensions=session.get("completed_dimensions", []),
        progress=session.get("progress", 0.0),
    )


@router.get("/review/report/{session_id}", response_model=ReviewReport)
async def get_review_report(session_id: str):
    """Get complete review report."""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    session = sessions[session_id]
    if session.get("status") != "completed":
        raise HTTPException(status_code=400, detail="Review not completed")

    report = session.get("report", {})

    return ReviewReport(
        project_name=report.get("project_name", "PRD Review"),
        version=report.get("version", "v1.0"),
        review_date=report.get("review_date", "2026-03-27"),
        preset=session.get("preset", "normal"),
        total_score=report.get("total_score", 0.0),
        recommendation=report.get("recommendation", "PENDING"),
        dimension_scores=report.get("dimension_scores", []),
        issues=report.get("issues", []),
        summary=report.get("summary", "Report not available"),
    )
