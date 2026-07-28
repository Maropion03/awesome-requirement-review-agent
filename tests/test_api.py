import json
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from backend.app import app


class FakeClient:
    def __init__(self, credentials):
        self.credentials = credentials

    async def complete(self, *, system, user, max_tokens=2200):
        return json.dumps({"score": 8, "issues": [], "reasoning": "ok"}, ensure_ascii=False)

    async def validate(self):
        return None


class ApiTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_provider_catalog_contains_no_secret_or_editable_base_url(self):
        response = self.client.get("/api/providers")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["max_upload_bytes"], 3_500_000)
        self.assertEqual(payload["max_document_chars"], 80_000)
        self.assertNotIn("base_url", payload["providers"][0])
        self.assertNotIn("api_key", json.dumps(payload))

    def test_review_stream_is_single_request_and_returns_terminal_event(self):
        with patch("backend.core.pipeline.LLMClient", FakeClient):
            response = self.client.post(
                "/api/review/run",
                files={"file": ("demo.md", b"# Demo PRD\nA sufficiently detailed product requirement document.", "text/markdown")},
                data={"provider": "minimax", "api_key": "private-key", "model": "MiniMax-M2.7", "preset": "normal"},
            )
        self.assertEqual(response.status_code, 200)
        events = [json.loads(line) for line in response.text.splitlines()]
        self.assertEqual(events[0]["event"], "connected")
        self.assertEqual(events[-1]["event"], "complete")
        self.assertNotIn("private-key", response.text)

    def test_bad_file_and_bad_key_fail_before_streaming(self):
        response = self.client.post(
            "/api/review/run",
            files={"file": ("demo.txt", b"not a prd", "text/plain")},
            data={"provider": "minimax", "api_key": "", "model": "MiniMax-M2.7", "preset": "normal"},
        )
        self.assertEqual(response.status_code, 422)

    def test_unknown_provider_and_preset_are_client_errors(self):
        provider_response = self.client.post(
            "/api/providers/validate",
            json={"provider": "custom", "api_key": "key", "model": "model"},
        )
        self.assertEqual(provider_response.status_code, 400)

        preset_response = self.client.post(
            "/api/review/run",
            files={"file": ("demo.md", b"# Demo PRD\nA sufficiently detailed product requirement document.", "text/markdown")},
            data={"provider": "minimax", "api_key": "key", "model": "MiniMax-M2.7", "preset": "unknown"},
        )
        self.assertEqual(preset_response.status_code, 422)


if __name__ == "__main__":
    unittest.main()
