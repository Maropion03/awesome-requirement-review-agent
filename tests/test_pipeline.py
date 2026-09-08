import asyncio
import json
import unittest

from backend.core.models import ProviderCredentials
from backend.core.pipeline import PRESET_WEIGHTS, build_report, review_dimension, stream_review


class FakeConcurrentClient:
    def __init__(self, fail_dimension=None):
        self.active = 0
        self.max_active = 0
        self.fail_dimension = fail_dimension

    async def complete(self, *, system, user, max_tokens=2200, images=None):
        self.active += 1
        self.max_active = max(self.max_active, self.active)
        await asyncio.sleep(0.01)
        self.active -= 1
        if self.fail_dimension and f"评审维度：{self.fail_dimension}" in user:
            raise RuntimeError("upstream response leaked")
        return json.dumps({
            "score": 8.0,
            "issues": [{
                "severity": "MEDIUM",
                "title": "缺少失败场景",
                "location": "验收标准",
                "description": "只覆盖成功路径",
                "suggestion": "补充失败与重试验收口径",
                "source_quote": "提交后显示成功",
            }],
            "reasoning": "结构基本完整，但异常路径不足",
        }, ensure_ascii=False)


class PipelineTests(unittest.IsolatedAsyncioTestCase):
    async def collect(self, client):
        credentials = ProviderCredentials(api_format="openai_chat", base_url="https://api.example.com/v1", api_key="key", model="model")
        raw_events = [chunk async for chunk in stream_review(
            credentials=credentials,
            prd_text="# Demo PRD\n## 验收标准\n提交后显示成功，并需要定义完整的业务目标。",
            preset="normal",
            client=client,
        )]
        return [json.loads(chunk) for chunk in raw_events]

    async def test_six_dimensions_execute_concurrently_and_emit_one_report(self):
        client = FakeConcurrentClient()
        events = await self.collect(client)
        report = next(event["report"] for event in events if event["event"] == "complete")
        self.assertGreater(client.max_active, 1)
        self.assertEqual(len([event for event in events if event["event"] == "dimension_start"]), 6)
        self.assertEqual(len(report["dimension_scores"]), 6)
        self.assertEqual(report["status"], "completed")
        self.assertEqual(report["total_score"], 80.0)

    async def test_one_dimension_failure_is_visible_and_does_not_hang_the_stream(self):
        events = await self.collect(FakeConcurrentClient(fail_dimension="技术可行性"))
        report = next(event["report"] for event in events if event["event"] == "complete")
        self.assertEqual(report["status"], "degraded_complete")
        self.assertEqual(report["degraded_dimensions"][0]["dimension"], "技术可行性")
        self.assertNotIn("upstream response leaked", json.dumps(report, ensure_ascii=False))

    async def test_diagram_pages_are_analyzed_once_and_reused_as_mermaid(self):
        class DiagramClient(FakeConcurrentClient):
            def __init__(self):
                super().__init__()
                self.vision_calls = 0
                self.review_prompts = []

            async def complete(self, *, system, user, max_tokens=2200, images=None):
                if images:
                    self.vision_calls += 1
                    return json.dumps({"diagrams": [{
                        "page": 6,
                        "title": "上架审批",
                        "nodes": ["提交申请", "管理员审批", "发布"],
                        "edges": [{"source": 0, "target": 1, "label": "提交"}, {"source": 1, "target": 2, "label": "同意"}],
                        "confidence": 0.9,
                        "unresolved_labels": [],
                    }]}, ensure_ascii=False)
                self.review_prompts.append(user)
                return await super().complete(system=system, user=user, max_tokens=max_tokens)

        review_client = DiagramClient()
        vision_client = DiagramClient()
        credentials = ProviderCredentials(api_format="openai_chat", base_url="https://api.example.com/v1", api_key="key", model="review-model")
        vision_credentials = ProviderCredentials(api_format="openai_chat", base_url="https://api.example.com/v1", api_key="key", model="vision-model")
        events = [json.loads(chunk) async for chunk in stream_review(
            credentials=credentials,
            vision_credentials=vision_credentials,
            prd_text="# Demo PRD\n提交后显示成功，并需要定义完整的业务目标。",
            preset="normal",
            client=review_client,
            vision_client=vision_client,
            diagram_images=[{"page": 6, "mime_type": "image/jpeg", "data": "ZmFrZQ=="}],
        )]
        report = next(event["report"] for event in events if event["event"] == "complete")
        connected = next(event for event in events if event["event"] == "connected")
        self.assertEqual(connected["vision_model"], "vision-model")
        self.assertEqual(vision_client.vision_calls, 1)
        self.assertEqual(review_client.vision_calls, 0)
        self.assertEqual(report["diagram_analysis"]["status"], "completed")
        self.assertIn("flowchart TD", report["diagram_analysis"]["mermaid"])
        self.assertTrue(all("视觉流程图识别" in prompt for prompt in review_client.review_prompts))

    async def test_closing_stream_cancels_outstanding_provider_calls(self):
        class BlockingClient:
            def __init__(self):
                self.started = 0
                self.cancelled = 0

            async def complete(self, **kwargs):
                self.started += 1
                try:
                    await asyncio.Event().wait()
                except asyncio.CancelledError:
                    self.cancelled += 1
                    raise

        client = BlockingClient()
        credentials = ProviderCredentials(api_format="openai_chat", base_url="https://api.example.com/v1", api_key="key", model="model")
        stream = stream_review(
            credentials=credentials,
            prd_text="# Demo PRD\nA sufficiently detailed product requirement document.",
            preset="normal",
            client=client,
        )
        for _ in range(8):
            await anext(stream)
        await asyncio.sleep(0)
        await stream.aclose()
        self.assertEqual(client.started, 6)
        self.assertEqual(client.cancelled, 6)


class DeterministicReporterTests(unittest.TestCase):
    def test_every_preset_weight_sum_is_one(self):
        for weights in PRESET_WEIGHTS.values():
            self.assertAlmostEqual(sum(weights.values()), 1.0)

    def test_report_uses_hundred_point_total_and_stable_issue_ids(self):
        from backend.core.models import DimensionReview

        result = DimensionReview.model_validate({
            "score": 10,
            "issues": [{"severity": "HIGH", "title": "A", "location": "目标", "description": "a", "suggestion": "fix", "source_quote": "quote"}],
            "reasoning": "ok",
        })
        report = build_report({"completeness": result}, {}, preset="normal", prd_text="# Demo\nA complete PRD body")
        self.assertLessEqual(report["total_score"], 100)
        self.assertEqual(report["issues"][0]["id"], "HIGH-1")
        self.assertTrue(report["issues"][0]["issue_key"].startswith("issue::"))


class EvidenceValidationTests(unittest.IsolatedAsyncioTestCase):
    async def test_non_verbatim_model_quote_is_removed(self):
        class HallucinatingClient:
            async def complete(self, **kwargs):
                return json.dumps({
                    "score": 7,
                    "issues": [{
                        "severity": "LOW",
                        "title": "A",
                        "location": "目标",
                        "description": "a",
                        "suggestion": "fix",
                        "source_quote": "原文中不存在的句子",
                    }],
                    "reasoning": "ok",
                }, ensure_ascii=False)

        _, result = await review_dimension(HallucinatingClient(), "completeness", "# Demo\n真实的产品需求原文。")
        self.assertEqual(result.issues[0].source_quote, "")


if __name__ == "__main__":
    unittest.main()
