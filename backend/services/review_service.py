"""
Review Service - manages the review workflow.
"""

import asyncio
import json
from datetime import date
from pathlib import Path
from typing import Optional, Dict, Any, AsyncGenerator

from agents.orchestrator import Orchestrator
from config.prompts import PRESETS, DIMENSION_PROMPTS, REVIEWER_BASE_PROMPT
from services.sse_service import SSEService
from tools.parser import PRDParser
from utils.minimax_client import get_minimax_client
from utils.report_utils import (
    calculate_weighted_total_score,
    determine_recommendation,
    format_report_summary,
    normalize_dimension_score,
    sort_and_renumber_issues,
)


class ReviewService:
    """Service for managing PRD review workflow."""

    def __init__(
        self,
        session_id: str,
        file_path: str,
        preset: str = "normal",
        model: str = "MiniMax-M2.7",
        api_key: Optional[str] = None,
        api_base: Optional[str] = None,
        sse_service: Optional[SSEService] = None,
    ):
        self.session_id = session_id
        self.file_path = file_path
        self.preset = preset
        self.model = model
        self.api_key = api_key
        self.api_base = api_base

        self.sse_service = sse_service or SSEService(session_id)
        self.parser = PRDParser()
        self.llm = None
        self.prd_content: str = ""
        self.orchestrator: Optional[Orchestrator] = None

        self._review_results: Dict[str, Dict[str, Any]] = {}
        self._is_running = False

    async def initialize(self):
        """Initialize the review service."""
        # Parse PRD content
        self.prd_content = self.parser.parse(self.file_path)

        # Initialize LLM
        self.llm = get_minimax_client(
            model=self.model,
            api_key=self.api_key,
            api_base=self.api_base,
            streaming=False,
        )
        self.orchestrator = Orchestrator(
            model=self.model,
            api_key=self.api_key,
            api_base=self.api_base,
            sse_service=self.sse_service,
        )

    async def start(self) -> Dict[str, Any]:
        """Start the review process."""
        if self._is_running:
            return {"status": "already_running"}

        self._is_running = True
        self._review_results = {}

        try:
            if not self.prd_content or not self.orchestrator:
                await self.initialize()

            result = await self.orchestrator.run_review(
                self.prd_content,
                preset=self.preset,
            )
            self._review_results = result.get("review_results", {})
            report = result.get("report", {})

            return {"status": "completed", "report": report}

        except Exception as e:
            raise
        finally:
            self._is_running = False

    async def _call_llm(self, prompt: str) -> str:
        """Call LLM for review."""
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            lambda: self.llm.invoke(prompt),
        )
        return result.content if hasattr(result, "content") else str(result)

    def _parse_review_result(self, result: str, dimension_key: str, dimension_name: str) -> Dict[str, Any]:
        """Parse the review result from LLM output."""
        try:
            # Try to find and extract JSON from the result
            json_str = result

            # Check for markdown code blocks
            if "```json" in result:
                json_str = result.split("```json")[1].split("```")[0]
            elif "```" in result:
                json_str = result.split("```")[1].split("```")[0]

            # Try to parse as JSON
            parsed = json.loads(json_str.strip())

            # Check if we got the expected structure
            if "score" in parsed and "issues" in parsed:
                return {
                    "dimension": dimension_name,
                    "score": parsed.get("score", 0),
                    "issues": parsed.get("issues", []),
                    "reasoning": parsed.get("reasoning", ""),
                }

            # If parsed JSON doesn't have expected fields, try finding JSON in reasoning
            if "reasoning" in parsed and isinstance(parsed["reasoning"], str):
                try:
                    inner = json.loads(parsed["reasoning"])
                    if "score" in inner and "issues" in inner:
                        return {
                            "dimension": dimension_name,
                            "score": inner.get("score", 0),
                            "issues": inner.get("issues", []),
                            "reasoning": inner.get("reasoning", parsed["reasoning"]),
                        }
                except json.JSONDecodeError:
                    pass

            # Fallback: score 0
            return {
                "dimension": dimension_name,
                "score": 0.0,
                "issues": [],
                "reasoning": f"解析失败: {result[:500]}",
            }
        except json.JSONDecodeError as e:
            return {
                "dimension": dimension_name,
                "score": 0.0,
                "issues": [],
                "reasoning": f"解析失败: {result[:500]}",
            }

    async def _generate_report(self) -> Dict[str, Any]:
        """Generate final report."""
        if not self.llm:
            return {}

        # Build report content
        preset_config = PRESETS.get(self.preset, PRESETS["normal"])
        total_score = calculate_weighted_total_score(self._review_results, preset_config)
        recommendation = determine_recommendation(total_score)

        # Collect all issues
        all_issues = []
        for dimension_key, result in self._review_results.items():
            for issue in result.get("issues", []):
                all_issues.append({
                    **issue,
                    "dimension": DIMENSION_PROMPTS.get(dimension_key, {}).get("name", dimension_key),
                })

        # Sort issues by severity and assign globally unique ids per severity.
        all_issues = sort_and_renumber_issues(all_issues)

        # Build dimension scores
        dimension_scores = []
        for dimension_key, result in self._review_results.items():
            dim_name = DIMENSION_PROMPTS.get(dimension_key, {}).get("name", dimension_key)
            weight = preset_config.get(dimension_key, preset_config.get("others", 0.1))
            dimension_scores.append({
                "dimension": dim_name,
                "score": self._normalize_score(result.get("score", 0)),
                "weight": weight,
                "issues_count": len(result.get("issues", [])),
                "reasoning": result.get("reasoning", ""),
            })

        report = {
            "project_name": "PRD Review",
            "version": "v1.0",
            "review_date": str(date.today()),
            "preset": self.preset,
            "total_score": total_score,
            "recommendation": recommendation,
            "dimension_scores": dimension_scores,
            "issues": all_issues,
            "summary": format_report_summary(total_score, recommendation, len(all_issues)),
        }

        return report

    def _normalize_score(self, score: Any) -> float:
        """Clamp raw scores into the expected 0-10 range."""
        return normalize_dimension_score(score)

    async def stream_events(self):
        """Stream SSE events."""
        async for event in self.sse_service.event_generator():
            yield event


def get_review_service(
    session_id: str,
    file_path: str,
    preset: str = "normal",
    sse_service: Optional[SSEService] = None,
) -> ReviewService:
    """Factory function to create a review service."""
    return ReviewService(
        session_id=session_id,
        file_path=file_path,
        preset=preset,
        sse_service=sse_service,
    )
