import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient


BACKEND_ROOT = Path(__file__).resolve().parents[1] / "backend"
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from api import routes
from main import app


class TestChatRoute(unittest.TestCase):
    def setUp(self):
        self.original_api_key = os.environ.get("MINIMAX_API_KEY")
        self.original_chat_model = os.environ.get("MINIMAX_CHAT_MODEL")
        os.environ.pop("MINIMAX_API_KEY", None)
        os.environ.pop("MINIMAX_CHAT_MODEL", None)
        routes.sessions.clear()
        routes.sessions["session-1"] = {
            "filename": "demo.md",
            "file_type": "markdown",
            "size": 10,
            "file_path": "uploads/demo.md",
            "status": "completed",
            "preset": "normal",
            "sse_service": None,
            "current_dimension": None,
            "completed_dimensions": [],
            "progress": 100.0,
            "dimension_scores": [],
            "report": {
                "total_score": 76.0,
                "recommendation": "修改后通过",
                "summary": "demo",
                "issues": [],
            },
        }
        self.client = TestClient(app)

    def tearDown(self):
        routes.sessions.clear()
        if self.original_api_key is None:
            os.environ.pop("MINIMAX_API_KEY", None)
        else:
            os.environ["MINIMAX_API_KEY"] = self.original_api_key

        if self.original_chat_model is None:
            os.environ.pop("MINIMAX_CHAT_MODEL", None)
        else:
            os.environ["MINIMAX_CHAT_MODEL"] = self.original_chat_model

    def test_chat_endpoint_returns_structured_response(self):
        with patch("services.chat_service.resolve_minimax_config", return_value={
            "model": "MiniMax-M2.7",
            "api_key": None,
            "api_base": "https://api.minimax.chat/v1",
        }):
            response = self.client.post(
                "/api/review/chat",
                json={
                    "session_id": "session-1",
                    "message": "帮我解释一下当前结论",
                    "selected_issue_id": None,
                    "context_mode": "default",
                },
            )

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertIn("message", body)
        self.assertEqual(body["response_mode"], "report_level")
        self.assertEqual(body["assistant_status"], "unavailable")
        self.assertIn("suggested_actions", body)
        self.assertIn("run_state", body)


if __name__ == "__main__":
    unittest.main()
