"""API-format catalog and dependency-light LLM HTTP client."""

from __future__ import annotations

import asyncio
import ipaddress
import socket
from dataclasses import dataclass
from typing import Any, Callable
from urllib.parse import urlsplit

import httpx

from .models import ProviderCredentials


@dataclass(frozen=True)
class APIFormatSpec:
    id: str
    name: str
    protocol: str
    default_base_url: str
    default_model: str
    key_hint: str
    endpoint_hint: str

    def public_dict(self) -> dict[str, str]:
        return {
            "id": self.id,
            "name": self.name,
            "protocol": self.protocol,
            "default_base_url": self.default_base_url,
            "default_model": self.default_model,
            "key_hint": self.key_hint,
            "endpoint_hint": self.endpoint_hint,
        }


API_FORMATS: dict[str, APIFormatSpec] = {
    "openai_chat": APIFormatSpec(
        id="openai_chat",
        name="OpenAI Chat Completions",
        protocol="openai_chat",
        default_base_url="https://api.openai.com/v1",
        default_model="gpt-5.2",
        key_hint="API Key",
        endpoint_hint="/chat/completions",
    ),
    "openai_responses": APIFormatSpec(
        id="openai_responses",
        name="OpenAI Responses",
        protocol="openai_responses",
        default_base_url="https://api.openai.com/v1",
        default_model="gpt-5.2",
        key_hint="API Key",
        endpoint_hint="/responses",
    ),
    "anthropic_messages": APIFormatSpec(
        id="anthropic_messages",
        name="Anthropic Messages",
        protocol="anthropic_messages",
        default_base_url="https://api.anthropic.com",
        default_model="claude-sonnet-5",
        key_hint="API Key",
        endpoint_hint="/v1/messages",
    ),
}


class ProviderError(RuntimeError):
    """Safe, user-facing upstream error with no credentials or response body."""


def get_api_format(api_format: str) -> APIFormatSpec:
    spec = API_FORMATS.get(api_format.strip().lower())
    if not spec:
        raise ProviderError("暂不支持该 API 接口格式")
    return spec


def build_endpoint_url(base_url: str, api_format: str) -> str:
    base = base_url.rstrip("/")
    if api_format == "openai_chat":
        return f"{base}/chat/completions"
    if api_format == "openai_responses":
        return f"{base}/responses"
    if api_format == "anthropic_messages":
        suffix = "/messages" if urlsplit(base).path.rstrip("/").endswith("/v1") else "/v1/messages"
        return f"{base}{suffix}"
    raise ProviderError("暂不支持该 API 接口格式")


async def validate_public_base_url(
    base_url: str,
    *,
    resolver: Callable[..., list[tuple[Any, ...]]] | None = None,
) -> None:
    hostname = urlsplit(base_url).hostname
    if not hostname:
        raise ProviderError("Base URL 格式无效")
    try:
        literal = ipaddress.ip_address(hostname)
    except ValueError:
        literal = None
    if literal is not None:
        if not literal.is_global:
            raise ProviderError("Base URL 不能指向本机或内网")
        return

    lookup = resolver or socket.getaddrinfo
    try:
        records = await asyncio.wait_for(
            asyncio.to_thread(lookup, hostname, 443, type=socket.SOCK_STREAM),
            timeout=5,
        )
    except (TimeoutError, socket.gaierror, OSError):
        raise ProviderError("Base URL 域名无法解析") from None
    addresses = {record[4][0] for record in records if len(record) > 4 and record[4]}
    try:
        has_unsafe_address = any(not ipaddress.ip_address(address).is_global for address in addresses)
    except ValueError:
        has_unsafe_address = True
    if not addresses or has_unsafe_address:
        raise ProviderError("Base URL 不能解析到本机或内网地址")


def _safe_error(status_code: int) -> ProviderError:
    if status_code in {401, 403}:
        return ProviderError("API Key 无效或没有所选模型的访问权限")
    if status_code == 402:
        return ProviderError("API 账户余额不足")
    if status_code == 404:
        return ProviderError("接口路径或模型不存在")
    if status_code == 429:
        return ProviderError("模型请求过于频繁，请稍后重试")
    if 300 <= status_code < 400:
        return ProviderError("Base URL 返回重定向，已拒绝继续发送 API Key")
    if status_code >= 500:
        return ProviderError("模型服务暂时不可用，请稍后重试")
    return ProviderError(f"模型服务拒绝了请求（HTTP {status_code}）")


def _join_text_blocks(blocks: Any, *, text_type: str) -> str:
    if isinstance(blocks, str):
        return blocks
    if not isinstance(blocks, list):
        return ""
    return "\n".join(
        block.get("text", "")
        for block in blocks
        if isinstance(block, dict) and block.get("type") == text_type and isinstance(block.get("text"), str)
    )


class LLMClient:
    def __init__(
        self,
        credentials: ProviderCredentials,
        *,
        transport: httpx.AsyncBaseTransport | None = None,
        resolver: Callable[..., list[tuple[Any, ...]]] | None = None,
        timeout_seconds: float = 90.0,
    ) -> None:
        self.credentials = credentials
        self.api_format = get_api_format(credentials.api_format)
        self.transport = transport
        self.resolver = resolver
        self.timeout = httpx.Timeout(timeout_seconds, connect=15.0)

    async def complete(self, *, system: str, user: str, max_tokens: int = 2200, images: list[dict[str, str]] | None = None) -> str:
        for attempt in range(2):
            try:
                return await self._complete_once(system=system, user=user, max_tokens=max_tokens, images=images or [])
            except ProviderError:
                raise
            except (httpx.TimeoutException, httpx.NetworkError):
                if attempt == 1:
                    raise ProviderError("连接模型服务超时，请检查网络后重试") from None
                await asyncio.sleep(0.35)
        raise ProviderError("模型服务未返回结果")

    async def _complete_once(self, *, system: str, user: str, max_tokens: int, images: list[dict[str, str]]) -> str:
        await validate_public_base_url(self.credentials.base_url, resolver=self.resolver)
        api_key = self.credentials.api_key.get_secret_value()
        api_format = self.credentials.api_format
        url = build_endpoint_url(self.credentials.base_url, api_format)
        headers = {"content-type": "application/json"}

        if api_format == "anthropic_messages":
            headers.update({"x-api-key": api_key, "anthropic-version": "2023-06-01"})
            payload: dict[str, Any] = {
                "model": self.credentials.model,
                "max_tokens": max_tokens,
                "system": system,
                "messages": [{"role": "user", "content": [
                    {"type": "text", "text": user},
                    *[{"type": "image", "source": {"type": "base64", "media_type": image["mime_type"], "data": image["data"]}} for image in images],
                ] if images else user}],
            }
        elif api_format == "openai_responses":
            headers["authorization"] = f"Bearer {api_key}"
            payload = {
                "model": self.credentials.model,
                "instructions": system,
                "input": [{"role": "user", "content": [
                    {"type": "input_text", "text": user},
                    *[{"type": "input_image", "image_url": f"data:{image['mime_type']};base64,{image['data']}"} for image in images],
                ]}] if images else user,
                "max_output_tokens": max_tokens,
                "store": False,
            }
        else:
            headers["authorization"] = f"Bearer {api_key}"
            payload = {
                "model": self.credentials.model,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": [
                        {"type": "text", "text": user},
                        *[{"type": "image_url", "image_url": {"url": f"data:{image['mime_type']};base64,{image['data']}"}} for image in images],
                    ] if images else user},
                ],
                "max_completion_tokens": max_tokens,
            }

        async with httpx.AsyncClient(
            transport=self.transport,
            timeout=self.timeout,
            follow_redirects=False,
            trust_env=False,
        ) as client:
            response = await client.post(url, headers=headers, json=payload)
        if not response.is_success:
            raise _safe_error(response.status_code)

        try:
            data = response.json()
            if api_format == "anthropic_messages":
                content = _join_text_blocks(data.get("content"), text_type="text")
            elif api_format == "openai_responses":
                content = data.get("output_text", "")
                if not content:
                    content = "\n".join(
                        _join_text_blocks(item.get("content"), text_type="output_text")
                        for item in data.get("output", [])
                        if isinstance(item, dict) and item.get("type") == "message"
                    )
            else:
                content = _join_text_blocks(data["choices"][0]["message"]["content"], text_type="text")
        except (KeyError, IndexError, TypeError, ValueError, AttributeError):
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
