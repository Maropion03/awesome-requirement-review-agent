"""In-memory PRD parser for stateless serverless requests."""

from __future__ import annotations

from io import BytesIO
from pathlib import Path
from zipfile import BadZipFile, ZipFile

from docx import Document
from docx.table import Table
from docx.text.paragraph import Paragraph
from pypdf import PdfReader
from pypdf.errors import PdfReadError


MAX_UPLOAD_BYTES = 3_500_000
MAX_DOCUMENT_CHARS = 80_000
MAX_DOCX_UNCOMPRESSED_BYTES = 25_000_000
ALLOWED_EXTENSIONS = {".md", ".docx", ".pdf"}


class DocumentError(ValueError):
    pass


def _parse_docx(content: bytes) -> str:
    try:
        with ZipFile(BytesIO(content)) as archive:
            if sum(item.file_size for item in archive.infolist()) > MAX_DOCX_UNCOMPRESSED_BYTES:
                raise DocumentError("DOCX 解压后内容过大")
    except BadZipFile as error:
        raise DocumentError("文档无法解析，请确认文件没有损坏") from error

    document = Document(BytesIO(content))
    lines: list[str] = []
    for block in document.iter_inner_content():
        if isinstance(block, Paragraph):
            if block.text.strip():
                lines.append(block.text)
        elif isinstance(block, Table):
            for row in block.rows:
                cells = [" ".join(paragraph.text for paragraph in cell.paragraphs).strip() for cell in row.cells]
                if any(cells):
                    lines.append(" | ".join(cells))
    return "\n".join(lines)


def _parse_pdf(content: bytes) -> str:
    try:
        reader = PdfReader(BytesIO(content), strict=False)
        if reader.is_encrypted and not reader.decrypt(""):
            raise DocumentError("PDF 已加密，请移除密码后重新上传")

        lines: list[str] = []
        extracted_chars = 0
        for page in reader.pages:
            page_text = (page.extract_text() or "").strip()
            if not page_text:
                continue
            extracted_chars += len(page_text)
            if extracted_chars > MAX_DOCUMENT_CHARS:
                raise DocumentError("文档正文不能超过 8 万字符，请拆分后评审")
            lines.append(page_text)
    except DocumentError:
        raise
    except (PdfReadError, ValueError, OSError, TypeError) as error:
        raise DocumentError("PDF 无法解析，请确认文件没有损坏或加密") from error

    text = "\n".join(lines)
    if len(text) < 20:
        raise DocumentError("PDF 未提取到足够文本；扫描件请先完成 OCR 后重新上传")
    return text


def parse_document(filename: str, content: bytes) -> str:
    suffix = Path(filename or "").suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise DocumentError("仅支持 .md、.docx 和 .pdf 文档")
    if not content:
        raise DocumentError("文档内容为空")
    if len(content) > MAX_UPLOAD_BYTES:
        raise DocumentError("文档不能超过 3.5MB")

    try:
        if suffix == ".md":
            text = content.decode("utf-8-sig")
        elif suffix == ".docx":
            text = _parse_docx(content)
        else:
            text = _parse_pdf(content)
    except DocumentError:
        raise
    except (UnicodeDecodeError, ValueError, OSError) as error:
        raise DocumentError("文档无法解析，请确认文件没有损坏") from error

    text = text.strip()
    if len(text) < 20:
        raise DocumentError("文档内容过短，无法进行有效评审")
    if len(text) > MAX_DOCUMENT_CHARS:
        raise DocumentError("文档正文不能超过 8 万字符，请拆分后评审")
    return text
