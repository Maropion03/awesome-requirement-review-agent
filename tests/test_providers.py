import json
import socket
import unittest

import httpx

from backend.core.models import ProviderCredentials
from backend.core.providers import (
    API_FORMATS,
    LLMClient,
    ProviderError,
    build_endpoint_url,
    validate_public_base_url,
)


def public_resolver(host, port, **kwargs):
    return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", port))]


class APIFormatCatalogTests(unittest.TestCase):
    def test_catalog_exposes_three_formats_and_editable_defaults(self):
        self.assertEqual(set(API_FORMATS), {"openai_chat", "openai_responses", "anthropic_messages"})
        self.assertEqual(API_FORMATS["openai_chat"].endpoint_hint, "/chat/completions")
        self.assertEqual(API_FORMATS["openai_responses"].endpoint_hint, "/responses")
        self.assertEqual(API_FORMATS["anthropic_messages"].endpoint_hint, "/v1/messages")

    def test_credentials_reject_bad_keys_and_unsafe_urls(self):
        with self.assertRaises(ValueError):
            ProviderCredentials(api_format="openai_chat", base_url="https://api.example.com/v1", api_key="  ", model="model")
        with self.assertRaises(ValueError):
            ProviderCredentials(api_format="openai_chat", base_url="http://api.example.com/v1", api_key="key", model="model")
        with self.assertRaises(ValueError):
            ProviderCredentials(api_format="openai_chat", base_url="https://127.0.0.1/v1", api_key="key", model="model")
        with self.assertRaises(ValueError):
            ProviderCredentials(api_format="openai_chat", base_url="https://user:pass@api.example.com/v1", api_key="key", model="model")

    def test_endpoint_paths_are_format_specific(self):
        self.assertEqual(build_endpoint_url("https://api.example.com/v1", "openai_chat"), "https://api.example.com/v1/chat/completions")
        self.assertEqual(build_endpoint_url("https://api.example.com/v1", "openai_responses"), "https://api.example.com/v1/responses")
        self.assertEqual(build_endpoint_url("https://api.example.com", "anthropic_messages"), "https://api.example.com/v1/messages")
        self.assertEqual(build_endpoint_url("https://api.example.com/v1", "anthropic_messages"), "https://api.example.com/v1/messages")


class BaseURLSecurityTests(unittest.IsolatedAsyncioTestCase):
    async def test_public_dns_is_allowed(self):
        await validate_public_base_url("https://api.example.com/v1", resolver=public_resolver)

    async def test_private_dns_is_rejected(self):
        def private_resolver(host, port, **kwargs):
            return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("10.0.0.8", port))]

        with self.assertRaisesRegex(ProviderError, "内网"):
            await validate_public_base_url("https://api.example.com/v1", resolver=private_resolver)


class APIFormatRequestTests(unittest.IsolatedAsyncioTestCase):
    async def test_openai_chat_contract(self):
        captured = {}

        async def handler(request: httpx.Request) -> httpx.Response:
            captured["url"] = str(request.url)
            captured["authorization"] = request.headers.get("authorization")
            captured["body"] = json.loads(request.content)
            return httpx.Response(200, json={"choices": [{"message": {"content": "OK"}}]})

        credentials = ProviderCredentials(api_format="openai_chat", base_url="https://api.example.com/v1", api_key="private-key", model="model")
        result = await LLMClient(credentials, transport=httpx.MockTransport(handler), resolver=public_resolver).complete(system="s", user="u")
        self.assertEqual(result, "OK")
        self.assertEqual(captured["url"], "https://api.example.com/v1/chat/completions")
        self.assertEqual(captured["authorization"], "Bearer private-key")
        self.assertEqual(captured["body"]["max_completion_tokens"], 2200)

    async def test_openai_responses_contract(self):
        captured = {}

        async def handler(request: httpx.Request) -> httpx.Response:
            captured["url"] = str(request.url)
            captured["body"] = json.loads(request.content)
            return httpx.Response(200, json={"output": [{"type": "message", "content": [{"type": "output_text", "text": "OK"}]}]})

        credentials = ProviderCredentials(api_format="openai_responses", base_url="https://api.example.com/v1", api_key="private-key", model="model")
        result = await LLMClient(credentials, transport=httpx.MockTransport(handler), resolver=public_resolver).complete(system="system", user="user")
        self.assertEqual(result, "OK")
        self.assertEqual(captured["url"], "https://api.example.com/v1/responses")
        self.assertEqual(captured["body"]["instructions"], "system")
        self.assertEqual(captured["body"]["input"], "user")
        self.assertEqual(captured["body"]["store"], False)
        self.assertEqual(captured["body"]["max_output_tokens"], 2200)

    async def test_anthropic_messages_contract(self):
        captured = {}

        async def handler(request: httpx.Request) -> httpx.Response:
            captured["url"] = str(request.url)
            captured["key"] = request.headers.get("x-api-key")
            captured["version"] = request.headers.get("anthropic-version")
            captured["body"] = json.loads(request.content)
            return httpx.Response(200, json={"content": [{"type": "text", "text": "OK"}]})

        credentials = ProviderCredentials(api_format="anthropic_messages", base_url="https://api.example.com", api_key="private-key", model="model")
        result = await LLMClient(credentials, transport=httpx.MockTransport(handler), resolver=public_resolver).complete(system="system", user="user")
        self.assertEqual(result, "OK")
        self.assertEqual(captured["url"], "https://api.example.com/v1/messages")
        self.assertEqual(captured["key"], "private-key")
        self.assertEqual(captured["version"], "2023-06-01")
        self.assertEqual(captured["body"]["system"], "system")

    async def test_redirect_and_upstream_errors_are_sanitized(self):
        async def redirect_handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(307, headers={"location": "https://127.0.0.1/secret"})

        credentials = ProviderCredentials(api_format="openai_chat", base_url="https://api.example.com/v1", api_key="private-key", model="model")
        with self.assertRaisesRegex(ProviderError, "重定向"):
            await LLMClient(credentials, transport=httpx.MockTransport(redirect_handler), resolver=public_resolver).complete(system="s", user="u")

        async def auth_handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(401, json={"error": "private-key appeared upstream"})

        with self.assertRaisesRegex(ProviderError, "API Key 无效") as context:
            await LLMClient(credentials, transport=httpx.MockTransport(auth_handler), resolver=public_resolver).complete(system="s", user="u")
        self.assertNotIn("private-key", str(context.exception))


if __name__ == "__main__":
    unittest.main()
