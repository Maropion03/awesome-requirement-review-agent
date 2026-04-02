import asyncio
import sys
import unittest
from pathlib import Path


BACKEND_ROOT = Path(__file__).resolve().parents[1] / "backend"
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from agents.reviewers import CompletenessReviewer


class TestReviewerErrorFormatting(unittest.IsolatedAsyncioTestCase):
    async def test_authentication_error_is_rewritten(self):
        reviewer = CompletenessReviewer(api_key="dummy", api_base="http://127.0.0.1:8002/v1")

        class FakeLLM:
            def invoke(self, prompt):
                raise Exception("Error code: 401 - authorized_error login fail (1004)")

        reviewer.llm = FakeLLM()

        with self.assertRaises(RuntimeError) as ctx:
            await reviewer.review("# Demo\n\n## 验收标准\n必须支持失败重试。")

        self.assertIn("MiniMax 认证失败", str(ctx.exception))
        self.assertIn("MINIMAX_API_KEY", str(ctx.exception))

    async def test_cluster_busy_error_is_retried_and_then_succeeds(self):
        reviewer = CompletenessReviewer(api_key="dummy", api_base="http://127.0.0.1:8002/v1")

        class FakeLLM:
            def __init__(self):
                self.calls = 0

            def invoke(self, prompt):
                self.calls += 1
                if self.calls == 1:
                    raise Exception("当前服务集群负载较高，请稍后重试，感谢您的耐心等待。 (2064)")
                return type("Result", (), {
                    "content": '{"score": 7.5, "issues": [], "reasoning": "ok"}'
                })()

        fake_llm = FakeLLM()
        reviewer.llm = fake_llm

        result = await reviewer.review("# Demo\n\n## 用户价值\n必须说明目标用户收益。")

        self.assertEqual(fake_llm.calls, 2)
        self.assertEqual(result["score"], 7.5)

    async def test_cluster_busy_error_is_rewritten_after_retry_exhausted(self):
        reviewer = CompletenessReviewer(api_key="dummy", api_base="http://127.0.0.1:8002/v1")

        class FakeLLM:
            def invoke(self, prompt):
                raise Exception("当前服务集群负载较高，请稍后重试，感谢您的耐心等待。 (2064)")

        reviewer.llm = FakeLLM()

        with self.assertRaises(RuntimeError) as ctx:
            await reviewer.review("# Demo\n\n## 用户价值\n必须说明目标用户收益。")

        self.assertIn("MiniMax 服务暂时繁忙", str(ctx.exception))
        self.assertIn("稍后重试", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
