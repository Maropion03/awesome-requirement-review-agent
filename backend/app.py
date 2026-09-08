"""FastAPI application for local development and Vercel Functions."""

from __future__ import annotations

import base64
import os
import re
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import ValidationError

from .core.models import ChatRequest, ProductContext, ProviderCredentials, ProviderValidationRequest
from .core.parser import DocumentError, MAX_DOCUMENT_CHARS, MAX_UPLOAD_BYTES, parse_document
from .core.pipeline import PRESET_WEIGHTS, answer_report_question, stream_review
from .core.providers import API_FORMATS, LLMClient, ProviderError, get_api_format


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


@app.get("/api/formats")
async def formats() -> dict[str, object]:
    return {
        "formats": [api_format.public_dict() for api_format in API_FORMATS.values()],
        "presets": list(PRESET_WEIGHTS),
        "max_upload_bytes": MAX_UPLOAD_BYTES,
        "max_document_chars": MAX_DOCUMENT_CHARS,
    }


@app.post("/api/formats/validate")
async def validate_format(payload: ProviderValidationRequest) -> dict[str, str]:
    try:
        get_api_format(payload.api_format)
        await LLMClient(payload).validate()
    except ProviderError as error:
        raise HTTPException(status_code=400, detail=str(error)) from None
    return {"status": "ok", "message": "连接成功，API Key 与模型可用"}


@app.post("/api/review/run")
async def run_review(
    file: UploadFile | None = File(None),
    diagram_images: list[UploadFile] = File(default=[]),
    document_text: str | None = Form(None),
    document_name: str = Form("PRD"),
    api_format: str = Form(...),
    base_url: str = Form(...),
    api_key: str = Form(...),
    model: str = Form(...),
    vision_model: str | None = Form(None),
    product_context: str | None = Form(None),
    preset: str = Form("normal"),
) -> StreamingResponse:
    try:
        credentials = ProviderCredentials(api_format=api_format, base_url=base_url, api_key=api_key, model=model)
        vision_credentials = ProviderCredentials(
            api_format=api_format,
            base_url=base_url,
            api_key=api_key,
            model=(vision_model or model),
        )
        get_api_format(credentials.api_format)
    except (ValidationError, ProviderError) as error:
        raise HTTPException(status_code=422, detail=str(error)) from None

    if preset not in PRESET_WEIGHTS:
        raise HTTPException(status_code=422, detail="未知评审预设")

    context = None
    if product_context:
        if len(product_context) > 30_000:
            raise HTTPException(status_code=422, detail="产品 Context 请求过大")
        try:
            context = ProductContext.model_validate_json(product_context)
        except ValidationError as error:
            raise HTTPException(status_code=422, detail=f"产品 Context 格式无效：{error}") from None

    if document_text is not None:
        cleaned = document_text.strip()
        if len(cleaned) < 20:
            raise HTTPException(status_code=422, detail="文档内容过短，无法进行有效评审")
        if len(cleaned) > MAX_DOCUMENT_CHARS:
            raise HTTPException(status_code=422, detail="文档正文不能超过 8 万字符，请拆分后评审")
        title = Path(document_name).stem[:120] or "PRD"
        prd_text = f"# {title}\n\n{cleaned}"
    elif file is not None:
        content = await file.read(MAX_UPLOAD_BYTES + 1)
        await file.close()
        try:
            prd_text = parse_document(file.filename or "", content)
        except DocumentError as error:
            raise HTTPException(status_code=422, detail=str(error)) from None
    else:
        raise HTTPException(status_code=422, detail="请选择一份 PRD 文档")

    prepared_images: list[dict[str, object]] = []
    if len(diagram_images) > 4:
        raise HTTPException(status_code=422, detail="流程图候选页面不能超过 4 页")
    for image in diagram_images:
        if image.content_type not in {"image/jpeg", "image/png"}:
            raise HTTPException(status_code=422, detail="流程图页面仅支持 JPEG 或 PNG")
        data = await image.read(700_001)
        await image.close()
        if len(data) > 700_000:
            raise HTTPException(status_code=422, detail="单张流程图页面不能超过 700KB")
        match = re.search(r"page-(\d+)", image.filename or "")
        prepared_images.append({
            "page": int(match.group(1)) if match else len(prepared_images) + 1,
            "mime_type": image.content_type,
            "data": base64.b64encode(data).decode("ascii"),
        })

    return StreamingResponse(
        stream_review(
            credentials=credentials,
            vision_credentials=vision_credentials,
            prd_text=prd_text,
            product_context=context,
            preset=preset,
            diagram_images=prepared_images,
        ),
        media_type="application/x-ndjson",
        headers={"Cache-Control": "no-store", "X-Content-Type-Options": "nosniff"},
    )


@app.post("/api/review/chat")
async def review_chat(payload: ChatRequest) -> dict[str, object]:
    try:
        get_api_format(payload.api_format)
        return await answer_report_question(
            credentials=payload,
            message=payload.message,
            report=payload.report,
            selected_issue_id=payload.selected_issue_id,
        )
    except ProviderError as error:
        raise HTTPException(status_code=400, detail=str(error)) from None
