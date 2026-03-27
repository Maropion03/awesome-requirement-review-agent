"""
Reporter Agent - generates final review report.
"""

import json
from datetime import date
from typing import Optional, Dict, Any, List

from crewai import Agent

from utils.minimax_client import get_minimax_client
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
        """Calculate weighted total score based on preset."""
        preset_config = PRESETS.get(preset, PRESETS["normal"])

        total_score = 0.0
        weight_sum = 0.0

        for dimension, result in review_results.items():
            if dimension in preset_config:
                weight = preset_config[dimension]
            else:
                weight = preset_config.get("others", 0.1)

            total_score += result.get("score", 0) * weight
            weight_sum += weight

        if weight_sum > 0:
            return round(total_score / weight_sum * 10, 1)
        return 0.0

    def determine_recommendation(self, total_score: float) -> str:
        """Determine recommendation based on total score."""
        if total_score >= 8.0:
            return "APPROVE"
        elif total_score >= 6.0:
            return "MODIFY"
        else:
            return "REJECT"

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

    def get_agent(self) -> Agent:
        """Get the underlying CrewAI Agent."""
        return self.agent
