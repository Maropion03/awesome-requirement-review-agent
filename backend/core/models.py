"""Validated API and review models."""

from __future__ import annotations

import json
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, SecretStr, field_validator, model_validator


class ProviderCredentials(BaseModel):
    model_config = ConfigDict(extra="forbid")

    provider: str = Field(min_length=1, max_length=32)
    api_key: SecretStr
    model: str = Field(min_length=1, max_length=160)

    @field_validator("provider", "model")
    @classmethod
    def validate_text_fields(cls, value: str) -> str:
        value = value.strip()
        if not value or any(ord(character) < 32 for character in value):
            raise ValueError("包含无效字符")
        return value

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
