import sys
import unittest
from pathlib import Path

from fastapi.testclient import TestClient


BACKEND_ROOT = Path(__file__).resolve().parents[1] / "backend"
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from api import routes
from main import app


class TestPdfExport(unittest.TestCase):
    def setUp(self):
        routes.sessions.clear()
        routes.sessions["session-pdf"] = {
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
                "project_name": "中文项目",
                "version": "v1.0",
                "review_date": "2026-04-02",
                "total_score": 83.0,
                "recommendation": "通过",
                "summary": "这是一份包含中文内容的摘要。",
                "dimension_scores": [
                    {"dimension": "完整性", "score": 8.5},
                    {"dimension": "可行性", "score": 8.0},
                ],
                "issues": [
                    {
                        "id": "HIGH-1",
                        "display_id": "HIGH-1",
                        "severity": "HIGH",
                        "title": "登录流程缺少异常分支",
                        "dimension": "完整性",
                        "description": "文档未覆盖短信验证码失败后的回退方案。",
                        "suggestion": "补充错误状态与重试限制。",
                    }
                ],
            },
        }
        self.client = TestClient(app)

    def tearDown(self):
        routes.sessions.clear()

    def test_pdf_export_registers_chinese_font(self):
        response = self.client.get("/api/review/export/pdf/session-pdf")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers.get("content-type"), "application/pdf")
        self.assertIn(b"STSong-Light", response.content)


if __name__ == "__main__":
    unittest.main()
