import sys
import unittest
from pathlib import Path


BACKEND_ROOT = Path(__file__).resolve().parents[1] / "backend"
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from agents.reporter import ReporterAgent
from services.review_service import ReviewService


class ReporterScoreTests(unittest.TestCase):
    def test_generate_report_caps_total_score_at_hundred_and_keeps_dimension_scale(self):
        reporter = ReporterAgent.__new__(ReporterAgent)

        review_results = {
            "completeness": {"score": 12.0, "issues": [], "reasoning": "ok", "dimension": "需求完整性"},
            "reasonableness": {"score": 12.0, "issues": [], "reasoning": "ok", "dimension": "需求合理性"},
            "user_value": {"score": 12.0, "issues": [], "reasoning": "ok", "dimension": "用户价值"},
            "feasibility": {"score": 12.0, "issues": [], "reasoning": "ok", "dimension": "技术可行性"},
            "risk": {"score": 12.0, "issues": [], "reasoning": "ok", "dimension": "实现风险"},
            "priority_consistency": {"score": 12.0, "issues": [], "reasoning": "ok", "dimension": "优先级一致性"},
        }

        report = reporter.generate_report(review_results, preset="normal")

        self.assertLessEqual(report["total_score"], 100.0)
        self.assertEqual(report["total_score"], 100.0)
        self.assertEqual(report["recommendation"], "通过")
        self.assertIn("100.0/100", report["summary"])
        self.assertTrue(all(dimension["score"] == 10.0 for dimension in report["dimension_scores"]))

    def test_generate_report_renumbers_issue_ids_after_aggregation(self):
        reporter = ReporterAgent.__new__(ReporterAgent)

        review_results = {
            "completeness": {
                "score": 8.0,
                "reasoning": "ok",
                "dimension": "需求完整性",
                "issues": [
                    {"id": "HIGH-1", "severity": "HIGH", "title": "A", "description": "a"},
                    {"id": "LOW-1", "severity": "LOW", "title": "B", "description": "b"},
                ],
            },
            "risk": {
                "score": 7.0,
                "reasoning": "ok",
                "dimension": "实现风险",
                "issues": [
                    {"id": "HIGH-1", "severity": "HIGH", "title": "C", "description": "c"},
                    {"id": "MEDIUM-1", "severity": "MEDIUM", "title": "D", "description": "d"},
                ],
            },
        }

        report = reporter.generate_report(review_results, preset="normal")

        self.assertEqual(
            [issue["id"] for issue in report["issues"]],
            ["HIGH-1", "HIGH-2", "MEDIUM-1", "LOW-1"],
        )
        self.assertTrue(all("display_id" in issue for issue in report["issues"]))
        self.assertTrue(all("issue_key" in issue for issue in report["issues"]))
        self.assertEqual(report["issues"][0]["dimension"], "需求完整性")
        self.assertEqual(report["issues"][1]["dimension"], "实现风险")

    def test_generate_report_exposes_evidence_for_each_issue(self):
        reporter = ReporterAgent.__new__(ReporterAgent)

        review_results = {
            "completeness": {
                "score": 7.0,
                "reasoning": "ok",
                "dimension": "需求完整性",
                "issues": [
                    {
                        "id": "HIGH-1",
                        "severity": "HIGH",
                        "title": "验收标准缺失",
                        "description": "未说明失败场景",
                        "suggestion": "补充失败重试与异常状态",
                        "source_quote": "验收标准：用户提交后显示成功",
                        "source_section": "验收标准",
                        "source_locator": "section:验收标准",
                    }
                ],
            }
        }

        report = reporter.generate_report(review_results, preset="normal")
        issue = report["issues"][0]
        self.assertIn("evidence", issue)
        evidence = issue["evidence"]
        self.assertEqual(evidence["issue_key"], issue["issue_key"])
        self.assertEqual(evidence["display_id"], issue["display_id"])
        self.assertEqual(evidence["source_quote"], "验收标准：用户提交后显示成功")
        self.assertEqual(evidence["source_section"], "验收标准")
        self.assertEqual(evidence["source_locator"], "section:验收标准")


class ReviewServiceReportTests(unittest.IsolatedAsyncioTestCase):
    async def test_generate_report_uses_hundred_point_total_and_chinese_recommendation(self):
        service = ReviewService(session_id="session-1", file_path="demo.md")
        service.llm = object()
        service._review_results = {
            "completeness": {"score": 8.0, "reasoning": "ok", "issues": []},
            "reasonableness": {"score": 8.0, "reasoning": "ok", "issues": []},
            "user_value": {"score": 8.0, "reasoning": "ok", "issues": []},
            "feasibility": {"score": 8.0, "reasoning": "ok", "issues": []},
            "risk": {"score": 8.0, "reasoning": "ok", "issues": []},
            "priority_consistency": {"score": 8.0, "reasoning": "ok", "issues": []},
        }

        report = await service._generate_report()

        self.assertEqual(report["total_score"], 80.0)
        self.assertEqual(report["recommendation"], "通过")
        self.assertIn("80.0/100", report["summary"])
        self.assertTrue(all(dimension["score"] == 8.0 for dimension in report["dimension_scores"]))

    async def test_generate_report_renumbers_issue_ids_after_aggregation(self):
        service = ReviewService(session_id="session-1", file_path="demo.md")
        service.llm = object()
        service._review_results = {
            "completeness": {
                "score": 8.0,
                "reasoning": "ok",
                "issues": [
                    {"id": "HIGH-1", "severity": "HIGH", "title": "A", "description": "a", "source_quote": "quote A", "source_section": "section A", "source_locator": "locator A"},
                    {"id": "LOW-1", "severity": "LOW", "title": "B", "description": "b"},
                ],
            },
            "risk": {
                "score": 7.0,
                "reasoning": "ok",
                "issues": [
                    {"id": "HIGH-1", "severity": "HIGH", "title": "C", "description": "c"},
                    {"id": "MEDIUM-1", "severity": "MEDIUM", "title": "D", "description": "d"},
                ],
            },
        }

        report = await service._generate_report()

        self.assertEqual(
            [issue["id"] for issue in report["issues"]],
            ["HIGH-1", "HIGH-2", "MEDIUM-1", "LOW-1"],
        )
        self.assertTrue(all("display_id" in issue for issue in report["issues"]))
        self.assertTrue(all("issue_key" in issue for issue in report["issues"]))
        self.assertEqual(report["issues"][0]["dimension"], "需求完整性")
        self.assertEqual(report["issues"][1]["dimension"], "实现风险")

        issue = report["issues"][0]
        self.assertIn("evidence", issue)
        evidence = issue["evidence"]
        self.assertEqual(evidence["issue_key"], issue["issue_key"])
        self.assertEqual(evidence["display_id"], issue["display_id"])
        self.assertEqual(evidence["source_quote"], "quote A")
        self.assertEqual(evidence["source_section"], "section A")
        self.assertEqual(evidence["source_locator"], "locator A")


if __name__ == "__main__":
    unittest.main()
