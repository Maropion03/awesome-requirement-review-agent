"""Provider catalog and small, dependency-light LLM HTTP client."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any

import httpx

from .models import ProviderCredentials


@dataclass(frozen=True)
class ProviderSpec:
    id: str
    name: str
    protocol: str
    base_url: str
    default_model: str
    key_hint: str

    def public_dict(self) -> dict[str, str]:
        return {
            "id": self.id,
            "name": self.name,
            "protocol": self.protocol,
            "default_model": self.default_model,
            "key_hint": self.key_hint,
        }


PROVIDERS: dict[str, ProviderSpec] = {
    "minimax": ProviderSpec(
        id="minimax",
        name="MiniMax",
        protocol="openai",
        base_url="https://api.minimax.io/v1",
        default_model="MiniMax-M2.7",
        key_hint="MiniMax API Key",
    ),
    "openai": ProviderSpec(
        id="openai",
        name="OpenAI",
        protocol="openai",
        base_url="https://api.openai.com/v1",
        default_model="gpt-5.2",
        key_hint="sk-...",
    ),
    "anthropic": ProviderSpec(
        id="anthropic",
        name="Anthropic",
        protocol="anthropic",
        base_url="https://api.anthropic.com",
        default_model="claude-sonnet-5",
        key_hint="sk-ant-...",
    ),
    "deepseek": ProviderSpec(
        id="deepseek",
        name="DeepSeek",
        protocol="openai",
        base_url="https://api.deepseek.com",
        default_model="deepseek-v4-flash",
        key_hint="sk-...",
    ),
    "gemini": ProviderSpec(
        id="gemini",
        name="Google Gemini",
        protocol="openai",
        base_url="https://generativelanguage.googleapis.com/v1beta/openai",
        default_model="gemini-3.6-flash",
        key_hint="Google AI API Key",
    ),
    "openrouter": ProviderSpec(
        id="openrouter",
        name="OpenRouter",
        protocol="openai",
        base_url="https://openrouter.ai/api/v1",
        default_model="~openai/gpt-latest",
        key_hint="sk-or-v1-...",
    ),
}


class ProviderError(RuntimeError):
    """Safe, user-facing upstream error with no provider response body."""


def get_provider(provider_id: str) -> ProviderSpec:
    provider = PROVIDERS.get(provider_id.strip().lower())
    if not provider:
        raise ProviderError("暂不支持该 API 供应商")
    return provider


def _safe_error(status_code: int) -> ProviderError:
    if status_code in {401, 403}:
        return ProviderError("API Key 无效或没有所选模型的访问权限")
    if status_code == 402:
        return ProviderError("API 账户余额不足")
    if status_code == 404:
        return ProviderError("模型不存在，或当前账户不可用")
    if status_code == 429:
        return ProviderError("模型请求过于频繁，请稍后重试")
    if status_code >= 500:
        return ProviderError("模型服务暂时不可用，请稍后重试")
    return ProviderError(f"模型服务拒绝了请求（HTTP {status_code}）")


class LLMClient:
    def __init__(
        self,
        credentials: ProviderCredentials,
        *,
        transport: httpx.AsyncBaseTransport | None = None,
        timeout_seconds: float = 90.0,
    ) -> None:
        self.credentials = credentials
        self.provider = get_provider(credentials.provider)
        self.transport = transport
        self.timeout = httpx.Timeout(timeout_seconds, connect=15.0)

    async def complete(
        self,
        *,
        system: str,
        user: str,
        max_tokens: int = 2200,
    ) -> str:
        attempts = 2
        for attempt in range(attempts):
            try:
                return await self._complete_once(system=system, user=user, max_tokens=max_tokens)
            except ProviderError:
                raise
            except (httpx.TimeoutException, httpx.NetworkError):
                if attempt + 1 == attempts:
                    raise ProviderError("连接模型服务超时，请检查网络后重试") from None
                await asyncio.sleep(0.35)
        raise ProviderError("模型服务未返回结果")

    async def _complete_once(self, *, system: str, user: str, max_tokens: int) -> str:
        api_key = self.credentials.api_key.get_secret_value()
        if self.provider.protocol == "anthropic":
            url = f"{self.provider.base_url}/v1/messages"
            headers = {
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            }
            payload: dict[str, Any] = {
                "model": self.credentials.model,
                "max_tokens": max_tokens,
                "system": system,
                "messages": [{"role": "user", "content": user}],
            }
        else:
            url = f"{self.provider.base_url}/chat/completions"
            headers = {
                "authorization": f"Bearer {api_key}",
                "content-type": "application/json",
            }
            payload = {
                "model": self.credentials.model,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
            }
            token_field = "max_completion_tokens" if self.provider.id == "openai" else "max_tokens"
            payload[token_field] = max_tokens

        async with httpx.AsyncClient(transport=self.transport, timeout=self.timeout) as client:
            response = await client.post(url, headers=headers, json=payload)

        if not response.is_success:
            raise _safe_error(response.status_code)

        try:
            data = response.json()
            if self.provider.protocol == "anthropic":
                text_parts = [
                    block.get("text", "")
                    for block in data.get("content", [])
                    if block.get("type") == "text"
                ]
                content = "\n".join(text_parts)
            else:
                content = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError, ValueError):
            raise ProviderError("模型返回了无法识别的响应") from None

        if not isinstance(content, str) or not content.strip():
            raise ProviderError("模型没有返回文本内容")
        return content.strip()

    async def validate(self) -> None:
        response = await self.complete(
            system="You are a connection check. Follow the user instruction exactly.",
            user="Reply with only: OK",
            max_tokens=64,
        )
        if not response:
            raise ProviderError("模型连接测试未返回结果")
