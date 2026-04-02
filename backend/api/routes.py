import uuid
import hashlib
import time
from pathlib import Path
from typing import Optional

import aiofiles
from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from sse_starlette.sse import EventSourceResponse

from api.schemas import (
    ChatRequest,
    ChatResponse,
    UploadResponse,
    StartReviewRequest,
    StartReviewResponse,
    ReviewStatus,
    ReviewReport,
    AgentConfigRequest,
    AgentConfigResponse,
    ResetResponse,
    ShareResponse,
)
from services.sse_service import SSEService
from services.chat_service import build_chat_response
from services.review_service import get_review_service
from config.prompts import DIMENSION_PROMPTS

router = APIRouter()

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)
TOTAL_DIMENSIONS = max(len(DIMENSION_PROMPTS), 1)

# In-memory session store (replace with Redis/DB in production)
sessions: dict[str, dict] = {}


def build_session_record(
    filename: str,
    file_type: str,
    size: int,
    file_path: str,
    sse_service: SSEService,
) -> dict:
    return {
        "filename": filename,
        "file_type": file_type,
        "size": size,
        "file_path": file_path,
        "status": "uploaded",
        "preset": "normal",
        "sse_service": sse_service,
        "current_dimension": None,
        "completed_dimensions": [],
        "progress": 0.0,
        "dimension_scores": [],
    }


def record_session_event(session_id: str, event_type: str, data: dict) -> None:
    session = sessions.get(session_id)
    if not session:
        return

    if event_type == "dimension_start":
        session["status"] = "reviewing"
        session["current_dimension"] = data.get("dimension")
        return

    if event_type == "dimension_complete":
        dimension = data.get("dimension")
        completed_dimensions = session.setdefault("completed_dimensions", [])
        if dimension and dimension not in completed_dimensions:
            completed_dimensions.append(dimension)

        dimension_scores = session.setdefault("dimension_scores", [])
        dimension_scores[:] = [
            item for item in dimension_scores
            if item.get("dimension") != dimension
        ]
        dimension_scores.append({
            "dimension": dimension,
            "score": data.get("score", 0.0),
            "issues_count": len(data.get("issues", [])),
        })

        session["status"] = "reviewing"
        session["current_dimension"] = dimension
        session["progress"] = round((len(completed_dimensions) / TOTAL_DIMENSIONS) * 100, 1)
        return

    if event_type == "complete":
        session["status"] = "completed"
        session["current_dimension"] = None
        session["progress"] = 100.0
        session["report"] = data.get("report", session.get("report", {}))
        return

    if event_type == "error":
        session["status"] = "error"
        session["current_dimension"] = None
        session["error"] = data.get("message", "Unknown error")


def attach_session_tracking(session_id: str, sse_service: SSEService) -> None:
    sse_service.subscribe(lambda event_type, data: record_session_event(session_id, event_type, data))


@router.post("/review/chat", response_model=ChatResponse)
async def chat_review(request: ChatRequest):
    """Answer follow-up questions about the current review session."""
    if request.session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    session = sessions[request.session_id]
    return ChatResponse(**build_chat_response(
        session=session,
        message=request.message,
        selected_issue_id=request.selected_issue_id,
        context_mode=request.context_mode,
    ))


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

    attach_session_tracking(session_id, sse_service)
    sessions[session_id] = build_session_record(
        filename=filename,
        file_type=file_type,
        size=len(content),
        file_path=str(file_path),
        sse_service=sse_service,
    )

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
            sessions[session_id]["progress"] = 100.0
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
    session["current_dimension"] = None
    session["completed_dimensions"] = []
    session["progress"] = 0.0
    session["dimension_scores"] = []
    session.pop("error", None)
    session.pop("report", None)

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


@router.post("/review/config", response_model=AgentConfigResponse)
async def save_agent_config(request: AgentConfigRequest):
    """Save agent configuration for a review session."""
    session_id = request.session_id

    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    session = sessions[session_id]
    session["agent_config"] = request.config.model_dump()

    return AgentConfigResponse(
        session_id=session_id,
        config=request.config,
        status="saved"
    )


@router.post("/review/reset", response_model=ResetResponse)
async def reset_session(session_id: str):
    """Reset a review session to allow re-review."""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    session = sessions[session_id]
    session["status"] = "uploaded"
    session["preset"] = session.get("preset", "normal")
    session["current_dimension"] = None
    session["completed_dimensions"] = []
    session["progress"] = 0.0
    session["dimension_scores"] = []
    session.pop("error", None)
    session.pop("report", None)

    return ResetResponse(
        session_id=session_id,
        status="reset",
        message="Session has been reset. Ready for new review."
    )


# In-memory share tokens store (replace with Redis/DB in production)
share_tokens: dict[str, dict] = {}


@router.post("/review/share", response_model=ShareResponse)
async def share_report(session_id: str):
    """Generate a shareable link for a completed review report."""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    session = sessions[session_id]
    if session.get("status") != "completed":
        raise HTTPException(status_code=400, detail="Review not completed yet")

    # Generate share token
    timestamp = str(int(time.time()))
    token_input = f"{session_id}-{timestamp}-{uuid.uuid4()}"
    share_token = hashlib.sha256(token_input.encode()).hexdigest()[:16]

    # Store token with session mapping
    share_tokens[share_token] = {
        "session_id": session_id,
        "created_at": timestamp,
    }

    return ShareResponse(
        share_token=share_token,
        share_url=f"/share/{share_token}",
        expires_in=7 * 24 * 60 * 60  # 7 days
    )


@router.get("/review/share/{share_token}")
async def get_shared_report(share_token: str):
    """Access a shared report via token."""
    if share_token not in share_tokens:
        raise HTTPException(status_code=404, detail="Share link not found or expired")

    token_data = share_tokens[share_token]
    session_id = token_data["session_id"]

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


@router.get("/review/export/pdf/{session_id}")
async def export_pdf(session_id: str):
    """Export review report as PDF."""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    session = sessions[session_id]
    if session.get("status") != "completed":
        raise HTTPException(status_code=400, detail="Review not completed")

    report = session.get("report", {})

    # Generate PDF using reportlab
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import mm
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.lib import colors
        from reportlab.lib.enums import TA_LEFT, TA_CENTER
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.cidfonts import UnicodeCIDFont
    except ImportError:
        raise HTTPException(status_code=500, detail="PDF library not installed")

    # Create PDF in memory
    import io
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=20*mm, leftMargin=20*mm, topMargin=20*mm, bottomMargin=20*mm)

    cjk_font_name = "STSong-Light"
    if cjk_font_name not in pdfmetrics.getRegisteredFontNames():
        pdfmetrics.registerFont(UnicodeCIDFont(cjk_font_name))

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontName=cjk_font_name,
        fontSize=18,
        spaceAfter=12,
        alignment=TA_CENTER,
        wordWrap='CJK',
    )
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontName=cjk_font_name,
        fontSize=14,
        spaceAfter=8,
        spaceBefore=12,
        wordWrap='CJK',
    )
    body_style = ParagraphStyle(
        'CustomBody',
        parent=styles['Normal'],
        fontName=cjk_font_name,
        fontSize=10,
        spaceAfter=6,
        leading=14,
        wordWrap='CJK',
    )

    story = []

    # Title
    story.append(Paragraph(f"PRD 评审报告: {report.get('project_name', 'PRD Review')}", title_style))
    story.append(Spacer(1, 10*mm))

    # Summary info
    story.append(Paragraph(f"版本: {report.get('version', 'v1.0')}", body_style))
    story.append(Paragraph(f"评审日期: {report.get('review_date', 'N/A')}", body_style))
    story.append(Paragraph(f"评审模式: {session.get('preset', 'normal')}", body_style))
    story.append(Paragraph(f"综合评分: {report.get('total_score', 0)}/100", body_style))
    story.append(Paragraph(f"评审建议: {report.get('recommendation', 'PENDING')}", body_style))
    story.append(Spacer(1, 10*mm))

    # Summary
    story.append(Paragraph("评审摘要", heading_style))
    story.append(Paragraph(report.get('summary', 'No summary available'), body_style))
    story.append(Spacer(1, 10*mm))

    # Dimension scores
    story.append(Paragraph("维度评分", heading_style))
    dimension_scores = report.get('dimension_scores', [])
    if dimension_scores:
        data = [["维度", "评分"]]
        for dim in dimension_scores:
            data.append([dim.get('dimension', 'N/A'), f"{dim.get('score', 0)}/10"])
        dim_table = Table(data, colWidths=[100*mm, 50*mm])
        dim_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3a2e47')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, -1), cjk_font_name),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f8f3ec')),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ]))
        story.append(dim_table)
    story.append(Spacer(1, 10*mm))

    # Issues
    story.append(Paragraph("问题列表", heading_style))
    issues = report.get('issues', [])
    if issues:
        for issue in issues:
            severity = issue.get('severity', 'LOW')
            story.append(Paragraph(
                f"[{issue.get('display_id', issue.get('id', 'N/A'))}] {issue.get('title', 'N/A')} ({severity})",
                body_style
            ))
            story.append(Paragraph(f"维度: {issue.get('dimension', 'N/A')}", body_style))
            story.append(Paragraph(f"描述: {issue.get('description', 'N/A')}", body_style))
            if issue.get('suggestion'):
                story.append(Paragraph(f"建议: {issue.get('suggestion')}", body_style))
            story.append(Spacer(1, 4*mm))
    else:
        story.append(Paragraph("未发现任何问题", body_style))

    # Build PDF
    doc.build(story)
    buffer.seek(0)

    # Save to file for serving
    pdf_dir = Path("uploads/pdfs")
    pdf_dir.mkdir(parents=True, exist_ok=True)
    pdf_path = pdf_dir / f"{session_id}.pdf"
    with open(pdf_path, "wb") as f:
        f.write(buffer.getvalue())

    return FileResponse(
        path=str(pdf_path),
        filename=f"PRD_Review_Report_{session_id[:8]}.pdf",
        media_type="application/pdf"
    )
