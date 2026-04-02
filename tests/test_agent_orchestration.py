import sys
import unittest
from pathlib import Path


BACKEND_ROOT = Path(__file__).resolve().parents[1] / "backend"
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from agents.orchestrator import Orchestrator
from api import routes
from services.review_service import ReviewService


class FakeSSE:
    def __init__(self):
        self.events = []

    async def push_dimension_start(self, dimension):
        self.events.append(("dimension_start", dimension))

    async def push_dimension_complete(self, dimension, score, issues):
        self.events.append(("dimension_complete", dimension, score, len(issues)))

    async def push_streaming(self, content):
        self.events.append(("streaming", content))

    async def push_complete(self, report):
        self.events.append(("complete", report["recommendation"]))

    async def push_error(self, message):
        self.events.append(("error", message))


class FakeReviewer:
    def __init__(self, name, score):
        self.dimension_info = {"name": name}
        self.score = score

    async def review(self, prd_content):
        return {
            "score": self.score,
            "issues": [{"id": f"{self.dimension_info['name']}-1", "severity": "LOW", "title": "demo"}],
            "reasoning": f"{self.dimension_info['name']} reasoning",
        }


class FakeReporter:
    def generate_report(self, review_results, preset="normal"):
        return {
            "project_name": "PRD Review",
            "version": "v1.0",
            "review_date": "2026-03-30",
            "preset": preset,
            "total_score": 8.3,
            "recommendation": "APPROVE",
            "dimension_scores": [],
            "issues": [],
            "summary": f"{len(review_results)} dimensions reviewed",
        }


class OrchestratorExecutionTests(unittest.IsolatedAsyncioTestCase):
    async def test_orchestrator_coordinates_reviewers_and_reporter(self):
        sse = FakeSSE()
        orchestrator = Orchestrator(
            reviewers={
                "completeness": FakeReviewer("需求完整性", 8.0),
                "risk": FakeReviewer("实现风险", 7.0),
            },
            reporter=FakeReporter(),
            sse_service=sse,
            dimension_order=["completeness", "risk"],
            enable_runtime_agent=False,
        )

        result = await orchestrator.run_review("demo prd", preset="normal")

        self.assertEqual(result["report"]["recommendation"], "APPROVE")
        self.assertEqual(set(result["review_results"].keys()), {"completeness", "risk"})
        self.assertIn(("dimension_start", "需求完整性"), sse.events)
        self.assertIn(("dimension_complete", "实现风险", 7.0, 1), sse.events)
        self.assertIn(("complete", "APPROVE"), sse.events)


class ReviewServiceDelegationTests(unittest.IsolatedAsyncioTestCase):
    async def test_review_service_delegates_to_orchestrator(self):
        class StubOrchestrator:
            called = False

            async def run_review(self, prd_content, preset="normal"):
                StubOrchestrator.called = True
                return {
                    "review_results": {"completeness": {"score": 8.0, "issues": [], "reasoning": "ok"}},
                    "report": {
                        "project_name": "PRD Review",
                        "version": "v1.0",
                        "review_date": "2026-03-30",
                        "preset": preset,
                        "total_score": 8.0,
                        "recommendation": "APPROVE",
                        "dimension_scores": [],
                        "issues": [],
                        "summary": "ok",
                    },
                }

        service = ReviewService(
            session_id="session-1",
            file_path="ignored.md",
            sse_service=FakeSSE(),
        )
        service.prd_content = "demo prd"
        service.orchestrator = StubOrchestrator()

        result = await service.start()

        self.assertTrue(StubOrchestrator.called)
        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["report"]["recommendation"], "APPROVE")


class SessionTrackingTests(unittest.TestCase):
    def setUp(self):
        self.session_id = "session-status"
        routes.sessions.clear()

    def tearDown(self):
        routes.sessions.clear()

    def test_record_session_event_updates_status_progress_and_dimensions(self):
        routes.sessions[self.session_id] = routes.build_session_record(
            filename="demo.md",
            file_type="markdown",
            size=10,
            file_path="uploads/demo.md",
            sse_service=FakeSSE(),
        )

        routes.record_session_event(self.session_id, "dimension_start", {"dimension": "需求完整性"})
        routes.record_session_event(
            self.session_id,
            "dimension_complete",
            {
                "dimension": "需求完整性",
                "score": 8.5,
                "issues": [{"id": "H-1", "severity": "HIGH"}],
            },
        )
        routes.record_session_event(self.session_id, "complete", {"report": {"total_score": 8.5}})

        session = routes.sessions[self.session_id]
        self.assertEqual(session["status"], "completed")
        self.assertEqual(session["current_dimension"], None)
        self.assertEqual(session["completed_dimensions"], ["需求完整性"])
        self.assertEqual(session["progress"], 100.0)
        self.assertEqual(
            session["dimension_scores"],
            [{"dimension": "需求完整性", "score": 8.5, "issues_count": 1}],
        )


if __name__ == "__main__":
    unittest.main()
