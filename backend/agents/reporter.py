"""
Reporter Agent - generates final review report.
"""

import json
from datetime import date
from typing import Optional, Dict, Any, List

from crewai import Agent

from utils.minimax_client import get_minimax_client
from utils.report_utils import (
    calculate_weighted_total_score,
    determine_recommendation,
    format_report_summary,
    normalize_dimension_score,
    sort_and_renumber_issues,
)
from config.prompts import REPORTER_PROMPT, PRESETS


class ReporterAgent:
    """Agent responsible for generating final review reports."""

    def __init__(
        self,
        model: str = "MiniMax-M2.7",
        api_key: Optional[str] = None,
        api_base: Optional[str] = None,
    ):
        self.llm = get_minimax_client(
            model=model,
            api_key=api_key,
            api_base=api_base,
            streaming=True,
        )

        self.agent = Agent(
            role="报告生成专家",
            goal="汇总评审结果，生成专业的评审报告",
            backstory=self._get_backstory(),
            verbose=True,
            llm=self.llm,
        )

    def _get_backstory(self) -> str:
        return """你是一个专业的咨询顾问，擅长将复杂分析结果整理成清晰的报告。

你有以下能力：
1. 准确汇总多个维度的评审结果
2. 客观评估 PRD 的整体质量
3. 识别最关键的问题和改进建议
4. 生成结构清晰、内容专业的评审报告"""

    def build_report_prompt(
        self,
        review_results: Dict[str, Dict[str, Any]],
        preset: str = "normal",
    ) -> str:
        """Build the prompt for report generation."""
        preset_config = PRESETS.get(preset, PRESETS["normal"])

        # Format review results for the prompt
        results_str = json.dumps(review_results, ensure_ascii=False, indent=2)

        # Format preset weights
        weights_str = "\n".join(
            f"- {k}: {v}" for k, v in preset_config.items()
        )

        return REPORTER_PROMPT.format(
            review_results=results_str,
            preset=preset,
            preset_weights=weights_str,
        )

    def calculate_weighted_score(
        self,
        review_results: Dict[str, Dict[str, Any]],
        preset: str = "normal",
    ) -> float:
        """Calculate weighted total score based on preset on a 0-100 scale."""
        preset_config = PRESETS.get(preset, PRESETS["normal"])
        return calculate_weighted_total_score(review_results, preset_config)

    def determine_recommendation(self, total_score: float) -> str:
        """Determine recommendation based on total score."""
        return determine_recommendation(total_score)

    def parse_result(self, result: str) -> Dict[str, Any]:
        """Parse the report result from LLM output."""
        try:
            if "```json" in result:
                result = result.split("```json")[1].split("```")[0]
            elif "```" in result:
                result = result.split("```")[1].split("```")[0]

            return json.loads(result.strip())
        except json.JSONDecodeError:
            # Fallback: create a basic report structure
            return {
                "project_name": "PRD Review",
                "version": "v1.0",
                "review_date": str(date.today()),
                "total_score": 0.0,
                "recommendation": "PENDING",
                "issues": [],
                "summary": f"报告生成失败: {result[:200]}",
            }

    def generate_report(
        self,
        review_results: Dict[str, Dict[str, Any]],
        preset: str = "normal",
    ) -> Dict[str, Any]:
        """Generate a deterministic final report from reviewer outputs."""
        total_score = self.calculate_weighted_score(review_results, preset)
        recommendation = self.determine_recommendation(total_score)

        all_issues = []
        dimension_scores = []

        for dimension_key, result in review_results.items():
            dimension_name = result.get("dimension", dimension_key)
            issues = result.get("issues", [])
            normalized_score = self._normalize_score(result.get("score", 0))
            for issue in issues:
                all_issues.append({
                    **issue,
                    "dimension": dimension_name,
                })

            dimension_scores.append({
                "dimension": dimension_name,
                "score": normalized_score,
                "weight": PRESETS.get(preset, PRESETS["normal"]).get(
                    dimension_key,
                    PRESETS.get(preset, PRESETS["normal"]).get("others", 0.1),
                ),
                "issues_count": len(issues),
                "reasoning": result.get("reasoning", ""),
            })

        all_issues = sort_and_renumber_issues(all_issues)

        summary = format_report_summary(total_score, recommendation, len(all_issues))

        return {
            "project_name": "PRD Review",
            "version": "v1.0",
            "review_date": str(date.today()),
            "preset": preset,
            "total_score": total_score,
            "recommendation": recommendation,
            "dimension_scores": dimension_scores,
            "issues": all_issues,
            "summary": summary,
        }

    def _normalize_score(self, score: Any) -> float:
        """Clamp raw scores into the expected 0-10 range."""
        return normalize_dimension_score(score)

    def get_agent(self) -> Agent:
        """Get the underlying CrewAI Agent."""
        return self.agent
