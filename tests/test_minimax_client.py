import os
import sys
import tempfile
import unittest
from pathlib import Path


BACKEND_ROOT = Path(__file__).resolve().parents[1] / "backend"
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from utils.minimax_client import resolve_minimax_config


class ResolveMiniMaxConfigTests(unittest.TestCase):
    def setUp(self):
        self.original_api_key = os.environ.get("MINIMAX_API_KEY")
        self.original_api_base = os.environ.get("MINIMAX_API_BASE")
        self.original_model = os.environ.get("MINIMAX_CHAT_MODEL")

    def tearDown(self):
        if self.original_api_key is None:
            os.environ.pop("MINIMAX_API_KEY", None)
        else:
            os.environ["MINIMAX_API_KEY"] = self.original_api_key

        if self.original_api_base is None:
            os.environ.pop("MINIMAX_API_BASE", None)
        else:
            os.environ["MINIMAX_API_BASE"] = self.original_api_base

        if self.original_model is None:
            os.environ.pop("MINIMAX_CHAT_MODEL", None)
        else:
            os.environ["MINIMAX_CHAT_MODEL"] = self.original_model

    def test_env_file_values_override_process_environment(self):
        os.environ["MINIMAX_API_KEY"] = "env-key"
        os.environ["MINIMAX_API_BASE"] = "https://env.example/v1"
        os.environ["MINIMAX_CHAT_MODEL"] = "env-model"

        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = Path(tmpdir) / ".env"
            env_file.write_text(
                "\n".join(
                    [
                        "MINIMAX_API_KEY=file-key",
                        "MINIMAX_API_BASE=https://file.example/v1",
                        "MINIMAX_CHAT_MODEL=file-model",
                    ]
                ),
                encoding="utf-8",
            )

            config = resolve_minimax_config(env_file=env_file)

        self.assertEqual(config["api_key"], "file-key")
        self.assertEqual(config["api_base"], "https://file.example/v1")
        self.assertEqual(config["model"], "file-model")


if __name__ == "__main__":
    unittest.main()
