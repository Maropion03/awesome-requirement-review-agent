import json
import unittest

import httpx

from backend.core.models import ProviderCredentials
from backend.core.providers import LLMClient, PROVIDERS, ProviderError


class ProviderCatalogTests(unittest.TestCase):
    def test_catalog_has_fixed_hosts_and_never_exposes_them_to_user_input(self):
        self.assertEqual(PROVIDERS["minimax"].base_url, "https://api.minimax.io/v1")
        self.assertEqual(PROVIDERS["anthropic"].protocol, "anthropic")
        self.assertNotIn("base_url", PROVIDERS["openai"].public_dict())

    def test_credentials_reject_blank_and_control_character_keys(self):
        with self.assertRaises(ValueError):
            ProviderCredentials(provider="openai", api_key="  ", model="gpt-5.2")
        with self.assertRaises(ValueError):
            ProviderCredentials(provider="openai", api_key="secret\nkey", model="gpt-5.2")


class ProviderRequestTests(unittest.IsolatedAsyncioTestCase):
    async def test_openai_compatible_request_uses_bearer_and_chat_completions(self):
        captured = {}

        async def handler(request: httpx.Request) -> httpx.Response:
            captured["url"] = str(request.url)
            captured["authorization"] = request.headers.get("authorization")
            captured["body"] = json.loads(request.content)
            return httpx.Response(200, json={"choices": [{"message": {"content": "OK"}}]})

        credentials = ProviderCredentials(provider="minimax", api_key="private-key", model="MiniMax-M2.7")
        result = await LLMClient(credentials, transport=httpx.MockTransport(handler)).complete(system="s", user="u")

        self.assertEqual(result, "OK")
        self.assertEqual(captured["url"], "https://api.minimax.io/v1/chat/completions")
        self.assertEqual(captured["authorization"], "Bearer private-key")
        self.assertEqual(captured["body"]["model"], "MiniMax-M2.7")

    async def test_anthropic_request_uses_messages_headers_and_top_level_system(self):
        captured = {}

        async def handler(request: httpx.Request) -> httpx.Response:
            captured["url"] = str(request.url)
            captured["key"] = request.headers.get("x-api-key")
            captured["version"] = request.headers.get("anthropic-version")
            captured["body"] = json.loads(request.content)
            return httpx.Response(200, json={"content": [{"type": "text", "text": "OK"}]})

        credentials = ProviderCredentials(provider="anthropic", api_key="private-key", model="claude-sonnet-5")
        result = await LLMClient(credentials, transport=httpx.MockTransport(handler)).complete(system="system", user="user")

        self.assertEqual(result, "OK")
        self.assertEqual(captured["url"], "https://api.anthropic.com/v1/messages")
        self.assertEqual(captured["key"], "private-key")
        self.assertEqual(captured["version"], "2023-06-01")
        self.assertEqual(captured["body"]["system"], "system")

    async def test_openai_uses_current_completion_token_field(self):
        captured = {}

        async def handler(request: httpx.Request) -> httpx.Response:
            captured["body"] = json.loads(request.content)
            return httpx.Response(200, json={"choices": [{"message": {"content": "OK"}}]})

        credentials = ProviderCredentials(provider="openai", api_key="private-key", model="gpt-5.2")
        await LLMClient(credentials, transport=httpx.MockTransport(handler)).complete(system="s", user="u")
        self.assertEqual(captured["body"]["max_completion_tokens"], 2200)
        self.assertNotIn("max_tokens", captured["body"])

    async def test_upstream_error_is_sanitized(self):
        async def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(401, json={"error": "private-key appeared in upstream body"})

        credentials = ProviderCredentials(provider="openai", api_key="private-key", model="gpt-5.2")
        with self.assertRaisesRegex(ProviderError, "API Key 无效") as context:
            await LLMClient(credentials, transport=httpx.MockTransport(handler)).complete(system="s", user="u")
        self.assertNotIn("private-key", str(context.exception))


if __name__ == "__main__":
    unittest.main()
