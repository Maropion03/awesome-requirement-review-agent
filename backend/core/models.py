"""Validated API and review models."""

from __future__ import annotations

import ipaddress
import json
from typing import Any, Literal
from urllib.parse import urlsplit, urlunsplit

from pydantic import BaseModel, ConfigDict, Field, SecretStr, field_validator, model_validator


APIFormat = Literal["openai_chat", "openai_responses", "anthropic_messages"]


class ProviderCredentials(BaseModel):
    model_config = ConfigDict(extra="forbid")

    api_format: APIFormat
    base_url: str = Field(min_length=1, max_length=2048)
    api_key: SecretStr
    model: str = Field(min_length=1, max_length=160)

    @field_validator("model")
    @classmethod
    def validate_text_fields(cls, value: str) -> str:
        value = value.strip()
        if not value or any(ord(character) < 32 for character in value):
            raise ValueError("包含无效字符")
        return value

    @field_validator("base_url")
    @classmethod
    def validate_base_url(cls, value: str) -> str:
        value = value.strip()
        if any(ord(character) < 32 for character in value):
            raise ValueError("Base URL 包含无效字符")
        try:
            parsed = urlsplit(value)
            port = parsed.port
        except ValueError as error:
            raise ValueError("Base URL 格式无效") from error
        if parsed.scheme.lower() != "https" or not parsed.hostname:
            raise ValueError("Base URL 必须使用公网 HTTPS")
        if parsed.username or parsed.password or parsed.query or parsed.fragment:
            raise ValueError("Base URL 不能包含凭据、查询参数或片段")
        if port not in {None, 443}:
            raise ValueError("Base URL 仅允许 HTTPS 443 端口")

        hostname = parsed.hostname.encode("idna").decode("ascii").lower()
        if hostname == "localhost" or hostname.endswith(".localhost"):
            raise ValueError("Base URL 不能指向本机或内网")
        try:
            address = ipaddress.ip_address(hostname)
        except ValueError:
            address = None
        if address is not None and not address.is_global:
            raise ValueError("Base URL 不能指向本机或内网")

        host = f"[{hostname}]" if ":" in hostname else hostname
        return urlunsplit(("https", host, parsed.path.rstrip("/"), "", ""))

    @field_validator("api_key")
    @classmethod
    def validate_api_key(cls, value: SecretStr) -> SecretStr:
        secret = value.get_secret_value().strip()
        if not secret:
            raise ValueError("API Key 不能为空")
        if len(secret) > 512 or any(ord(character) < 32 for character in secret):
            raise ValueError("API Key 格式无效")
        return SecretStr(secret)


class ProviderValidationRequest(ProviderCredentials):
    pass


class ReviewIssue(BaseModel):
    model_config = ConfigDict(extra="forbid")

    severity: Literal["HIGH", "MEDIUM", "LOW"]
    title: str = Field(min_length=1, max_length=160)
    location: str = Field(default="", max_length=240)
    description: str = Field(min_length=1, max_length=2000)
    suggestion: str = Field(min_length=1, max_length=2000)
    source_quote: str = Field(default="", max_length=1000)

    @field_validator("severity", mode="before")
    @classmethod
    def normalize_severity(cls, value: Any) -> str:
        return str(value or "LOW").strip().upper()


class DimensionReview(BaseModel):
    model_config = ConfigDict(extra="forbid")

    score: float = Field(ge=0, le=10)
    issues: list[ReviewIssue] = Field(default_factory=list, max_length=20)
    reasoning: str = Field(min_length=1, max_length=3000)


class DiagramEdge(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source: int = Field(ge=0)
    target: int = Field(ge=0)
    label: str = Field(default="", max_length=160)


class DiagramGraph(BaseModel):
    model_config = ConfigDict(extra="forbid")

    page: int = Field(ge=1)
    title: str = Field(default="流程图", max_length=160)
    nodes: list[str] = Field(min_length=2, max_length=80)
    edges: list[DiagramEdge] = Field(default_factory=list, max_length=160)
    confidence: float = Field(ge=0, le=1)
    unresolved_labels: list[str] = Field(default_factory=list, max_length=30)


class DiagramAnalysis(BaseModel):
    model_config = ConfigDict(extra="forbid")

    diagrams: list[DiagramGraph] = Field(default_factory=list, max_length=4)


class ChatRequest(ProviderCredentials):
    message: str = Field(min_length=1, max_length=4000)
    report: dict[str, Any]
    selected_issue_id: str | None = Field(default=None, max_length=160)

    @field_validator("message")
    @classmethod
    def validate_message(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("消息不能为空")
        return value

    @model_validator(mode="after")
    def limit_report_size(self) -> "ChatRequest":
        if len(json.dumps(self.report, ensure_ascii=False)) > 500_000:
            raise ValueError("报告上下文过大")
        return self
