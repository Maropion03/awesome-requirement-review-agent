"""FastAPI application for local development and Vercel Functions."""

from __future__ import annotations

import os

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import ValidationError

from .core.models import ChatRequest, ProviderCredentials, ProviderValidationRequest
from .core.parser import DocumentError, MAX_DOCUMENT_CHARS, MAX_UPLOAD_BYTES, parse_document
from .core.pipeline import PRESET_WEIGHTS, answer_report_question, stream_review
from .core.providers import LLMClient, PROVIDERS, ProviderError, get_provider


app = FastAPI(
    title="PRD Review API",
    version="2.0.0",
    docs_url="/api/docs",
    redoc_url=None,
    openapi_url="/api/openapi.json",
)

local_origins = [origin.strip() for origin in os.getenv("LOCAL_DEV_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",") if origin.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=local_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


@app.get("/api/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "architecture": "stateless-byok"}


@app.get("/api/providers")
async def providers() -> dict[str, object]:
    return {
        "providers": [provider.public_dict() for provider in PROVIDERS.values()],
        "presets": list(PRESET_WEIGHTS),
        "max_upload_bytes": MAX_UPLOAD_BYTES,
        "max_document_chars": MAX_DOCUMENT_CHARS,
    }


@app.post("/api/providers/validate")
async def validate_provider(payload: ProviderValidationRequest) -> dict[str, str]:
    try:
        get_provider(payload.provider)
        await LLMClient(payload).validate()
    except ProviderError as error:
        raise HTTPException(status_code=400, detail=str(error)) from None
    return {"status": "ok", "message": "连接成功，API Key 与模型可用"}


@app.post("/api/review/run")
async def run_review(
    file: UploadFile = File(...),
    provider: str = Form(...),
    api_key: str = Form(...),
    model: str = Form(...),
    preset: str = Form("normal"),
) -> StreamingResponse:
    try:
        credentials = ProviderCredentials(provider=provider, api_key=api_key, model=model)
        get_provider(credentials.provider)
    except (ValidationError, ProviderError) as error:
        raise HTTPException(status_code=422, detail=str(error)) from None

    if preset not in PRESET_WEIGHTS:
        raise HTTPException(status_code=422, detail="未知评审预设")

    content = await file.read(MAX_UPLOAD_BYTES + 1)
    await file.close()
    try:
        prd_text = parse_document(file.filename or "", content)
    except DocumentError as error:
        raise HTTPException(status_code=422, detail=str(error)) from None

    return StreamingResponse(
        stream_review(
            credentials=credentials,
            prd_text=prd_text,
            preset=preset,
        ),
        media_type="application/x-ndjson",
        headers={"Cache-Control": "no-store", "X-Content-Type-Options": "nosniff"},
    )


@app.post("/api/review/chat")
async def review_chat(payload: ChatRequest) -> dict[str, object]:
    try:
        get_provider(payload.provider)
        return await answer_report_question(
            credentials=payload,
            message=payload.message,
            report=payload.report,
            selected_issue_id=payload.selected_issue_id,
        )
    except ProviderError as error:
        raise HTTPException(status_code=400, detail=str(error)) from None
