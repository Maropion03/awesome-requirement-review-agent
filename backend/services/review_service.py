"""
Review Service - manages the review workflow.
"""

import asyncio
import json
from datetime import date
from pathlib import Path
from typing import Optional, Dict, Any, AsyncGenerator

from config.prompts import PRESETS, DIMENSION_PROMPTS, REVIEWER_BASE_PROMPT
from services.sse_service import SSEService
from tools.parser import PRDParser
from utils.minimax_client import get_minimax_client


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

    async def start(self) -> Dict[str, Any]:
        """Start the review process."""
        if self._is_running:
            return {"status": "already_running"}

        self._is_running = True
        self._review_results = {}

        try:
            await self.initialize()

            # Review each dimension
            for dimension_key in DIMENSION_PROMPTS.keys():
                dim_info = DIMENSION_PROMPTS[dimension_key]
                await self.sse_service.push_dimension_start(dim_info["name"])

                # Build prompt and run review
                prompt = REVIEWER_BASE_PROMPT.format(
                    context=self.prd_content,
                    dimension=dim_info["name"],
                )

                # Run LLM call
                result = await self._call_llm(prompt)
                parsed = self._parse_review_result(result, dimension_key, dim_info["name"])

                self._review_results[dimension_key] = parsed

                await self.sse_service.push_dimension_complete(
                    dimension=dim_info["name"],
                    score=parsed.get("score", 0),
                    issues=parsed.get("issues", []),
                )

            # Generate final report
            report = await self._generate_report()

            await self.sse_service.push_complete(report)

            return {"status": "completed", "report": report}

        except Exception as e:
            await self.sse_service.push_error(str(e))
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

        # Calculate total score
        total_score = 0.0
        weight_sum = 0.0

        for dimension_key, result in self._review_results.items():
            if dimension_key in preset_config:
                weight = preset_config[dimension_key]
            else:
                weight = preset_config.get("others", 0.1)
            total_score += result.get("score", 0) * weight
            weight_sum += weight

        if weight_sum > 0:
            total_score = round(total_score / weight_sum * 10, 1)

        # Determine recommendation
        if total_score >= 8.0:
            recommendation = "APPROVE"
        elif total_score >= 6.0:
            recommendation = "MODIFY"
        else:
            recommendation = "REJECT"

        # Collect all issues
        all_issues = []
        for dimension_key, result in self._review_results.items():
            for issue in result.get("issues", []):
                issue["dimension"] = DIMENSION_PROMPTS.get(dimension_key, {}).get("name", dimension_key)
                all_issues.append(issue)

        # Sort issues by severity
        severity_order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
        all_issues.sort(key=lambda x: severity_order.get(x.get("severity", "LOW"), 3))

        # Build dimension scores
        dimension_scores = []
        for dimension_key, result in self._review_results.items():
            dim_name = DIMENSION_PROMPTS.get(dimension_key, {}).get("name", dimension_key)
            weight = preset_config.get(dimension_key, preset_config.get("others", 0.1))
            dimension_scores.append({
                "dimension": dim_name,
                "score": result.get("score", 0),
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
            "summary": f"综合评分 {total_score}/10，建议：{recommendation}",
        }

        return report

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
