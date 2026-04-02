"""
Orchestrator Agent - coordinates review agents.
"""

import os
from typing import Optional, Dict, Any, Iterable

from crewai import Agent, Crew

from agents.reviewers import get_all_reviewers
from agents.reporter import ReporterAgent
from utils.minimax_client import get_minimax_client
from config.prompts import ORCHESTRATOR_PROMPT, DIMENSION_PROMPTS


class Orchestrator:
    """Main orchestrator agent for PRD review."""

    def __init__(
        self,
        model: str = "MiniMax-M2.7",
        api_key: Optional[str] = None,
        api_base: Optional[str] = None,
        reviewers: Optional[Dict[str, Any]] = None,
        reporter: Optional[Any] = None,
        sse_service: Optional[Any] = None,
        dimension_order: Optional[Iterable[str]] = None,
        enable_runtime_agent: bool = True,
    ):
        self.sse_service = sse_service
        self.dimension_order = list(dimension_order or DIMENSION_PROMPTS.keys())
        self.reviewers = reviewers or get_all_reviewers(
            model=model,
            api_key=api_key,
            api_base=api_base,
        )
        self.reporter = reporter or ReporterAgent(
            model=model,
            api_key=api_key,
            api_base=api_base,
        )

        self.llm = None
        self.agent = None
        if enable_runtime_agent:
            self.llm = get_minimax_client(
                model=model,
                api_key=api_key,
                api_base=api_base,
                streaming=True,
            )

            self.agent = Agent(
                role="评审协调者",
                goal="协调各评审 Agent，高效完成 PRD 评审任务",
                backstory=ORCHESTRATOR_PROMPT,
                verbose=True,
                allow_delegation=True,
                llm=self.llm,
            )

    def get_agent(self) -> Agent:
        """Get the underlying CrewAI Agent."""
        return self.agent

    async def run_review(self, prd_content: str, preset: str = "normal") -> Dict[str, Any]:
        """Run the full review through explicit orchestrator/reviewer/reporter stages."""
        review_results: Dict[str, Dict[str, Any]] = {}

        try:
            await self._push_streaming("Orchestrator Agent 已接管评审流程。")

            for dimension_key in self.dimension_order:
                reviewer = self.reviewers[dimension_key]
                dimension_name = reviewer.dimension_info.get("name", dimension_key)

                if self.sse_service:
                    await self.sse_service.push_dimension_start(dimension_name)
                await self._push_streaming(f"{dimension_name} Reviewer Agent 正在分析...")

                parsed = await reviewer.review(prd_content)
                parsed.setdefault("dimension", dimension_name)
                parsed.setdefault("score", 0.0)
                parsed.setdefault("issues", [])
                parsed.setdefault("reasoning", "")
                review_results[dimension_key] = parsed

                if self.sse_service:
                    await self.sse_service.push_dimension_complete(
                        dimension=dimension_name,
                        score=parsed.get("score", 0.0),
                        issues=parsed.get("issues", []),
                    )
                await self._push_streaming(
                    f"{dimension_name} Reviewer Agent 完成，发现 {len(parsed.get('issues', []))} 个问题。"
                )

            await self._push_streaming("Reporter Agent 正在汇总最终报告...")
            report = self.reporter.generate_report(review_results, preset=preset)

            if self.sse_service:
                await self.sse_service.push_complete(report)

            return {"review_results": review_results, "report": report}
        except Exception as exc:
            if self.sse_service:
                await self.sse_service.push_error(str(exc))
            raise

    async def _push_streaming(self, message: str) -> None:
        if self.sse_service:
            await self.sse_service.push_streaming(message)
