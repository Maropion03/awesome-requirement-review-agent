import json
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from backend.app import app


class FakeClient:
    def __init__(self, credentials):
        self.credentials = credentials

    async def complete(self, *, system, user, max_tokens=2200, images=None):
        return json.dumps({"score": 8, "issues": [], "reasoning": "ok"}, ensure_ascii=False)

    async def validate(self):
        return None


class ApiTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_format_catalog_contains_three_transport_contracts(self):
        response = self.client.get("/api/formats")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["max_upload_bytes"], 3_500_000)
        self.assertEqual(payload["max_document_chars"], 80_000)
        self.assertEqual(len(payload["formats"]), 3)
        self.assertIn("default_base_url", payload["formats"][0])
        self.assertNotIn("api_key", json.dumps(payload))

    def test_review_stream_is_single_request_and_returns_terminal_event(self):
        with patch("backend.core.pipeline.LLMClient", FakeClient):
            response = self.client.post(
                "/api/review/run",
                files={"file": ("demo.md", b"# Demo PRD\nA sufficiently detailed product requirement document.", "text/markdown")},
                data={"api_format": "openai_chat", "base_url": "https://api.example.com/v1", "api_key": "private-key", "model": "model", "preset": "normal"},
            )
        self.assertEqual(response.status_code, 200)
        events = [json.loads(line) for line in response.text.splitlines()]
        self.assertEqual(events[0]["event"], "connected")
        self.assertEqual(events[-1]["event"], "complete")
        self.assertNotIn("private-key", response.text)

    def test_review_accepts_a_separate_vision_model(self):
        with patch("backend.core.pipeline.LLMClient", FakeClient):
            response = self.client.post(
                "/api/review/run",
                files={"file": ("demo.md", b"# Demo PRD\nA sufficiently detailed product requirement document.", "text/markdown")},
                data={
                    "api_format": "openai_chat",
                    "base_url": "https://api.example.com/v1",
                    "api_key": "private-key",
                    "model": "review-model",
                    "vision_model": "vision-model",
                    "preset": "normal",
                },
            )
        self.assertEqual(response.status_code, 200)
        connected = json.loads(response.text.splitlines()[0])
        self.assertEqual(connected["model"], "review-model")
        self.assertEqual(connected["vision_model"], "vision-model")

    def test_review_accepts_validated_product_context_without_returning_its_content(self):
        with patch("backend.core.pipeline.LLMClient", FakeClient):
            response = self.client.post(
                "/api/review/run",
                files={"file": ("demo.md", b"# Demo PRD\nA sufficiently detailed product requirement document.", "text/markdown")},
                data={
                    "api_format": "openai_chat", "base_url": "https://api.example.com/v1", "api_key": "private-key",
                    "model": "model", "preset": "normal",
                    "product_context": json.dumps({"enabled": True, "product_overview": "private product background"}),
                },
            )
        self.assertEqual(response.status_code, 200)
        events = [json.loads(line) for line in response.text.splitlines()]
        report = events[-1]["report"]
        self.assertEqual(report["product_context"]["source_count"], 1)
        self.assertNotIn("private product background", json.dumps(report))

    def test_review_rejects_malformed_product_context(self):
        response = self.client.post(
            "/api/review/run",
            files={"file": ("demo.md", b"# Demo PRD\nA sufficiently detailed product requirement document.", "text/markdown")},
            data={
                "api_format": "openai_chat", "base_url": "https://api.example.com/v1", "api_key": "key",
                "model": "model", "preset": "normal", "product_context": '{"unknown": "field"}',
            },
        )
        self.assertEqual(response.status_code, 422)

    def test_bad_file_and_bad_key_fail_before_streaming(self):
        response = self.client.post(
            "/api/review/run",
            files={"file": ("demo.txt", b"not a prd", "text/plain")},
            data={"api_format": "openai_chat", "base_url": "https://api.example.com/v1", "api_key": "", "model": "model", "preset": "normal"},
        )
        self.assertEqual(response.status_code, 422)

    def test_unknown_format_and_preset_are_client_errors(self):
        format_response = self.client.post(
            "/api/formats/validate",
            json={"api_format": "custom", "base_url": "https://api.example.com/v1", "api_key": "key", "model": "model"},
        )
        self.assertEqual(format_response.status_code, 422)

        preset_response = self.client.post(
            "/api/review/run",
            files={"file": ("demo.md", b"# Demo PRD\nA sufficiently detailed product requirement document.", "text/markdown")},
            data={"api_format": "openai_chat", "base_url": "https://api.example.com/v1", "api_key": "key", "model": "model", "preset": "unknown"},
        )
        self.assertEqual(preset_response.status_code, 422)


if __name__ == "__main__":
    unittest.main()
