import unittest
import sys
from pathlib import Path

from fastapi.testclient import TestClient

BACKEND_ROOT = Path(__file__).resolve().parents[1] / "backend"
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from main import app


class TestCorsConfiguration(unittest.TestCase):
    def test_vite_dev_origin_is_allowed_for_upload_preflight(self):
        client = TestClient(app)
        response = client.options(
            "/api/review/upload",
            headers={
                "Origin": "http://127.0.0.1:5176",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "content-type",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers.get("access-control-allow-origin"), "http://127.0.0.1:5176")


if __name__ == "__main__":
    unittest.main()
