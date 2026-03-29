"""
Review Agents - 6 dimension reviewers.
"""

import json
from typing import Optional, Any, Dict

from crewai import Agent

from utils.minimax_client import get_minimax_client
from config.prompts import DIMENSION_PROMPTS, REVIEWER_BASE_PROMPT


class DimensionReviewer:
    """Base class for dimension reviewers."""

    def __init__(
        self,
        dimension: str,
        model: str = "MiniMax-M2.7",
        api_key: Optional[str] = None,
        api_base: Optional[str] = None,
    ):
        self.dimension = dimension
        self.dimension_info = DIMENSION_PROMPTS.get(dimension, {})

        self.llm = get_minimax_client(
            model=model,
            api_key=api_key,
            api_base=api_base,
            streaming=True,
        )

        self.agent = Agent(
            role=f"{self.dimension_info.get('name', dimension)}评审专家",
            goal=f"严格评审 PRD 的 {self.dimension_info.get('name', dimension)}，发现遗漏和模糊之处",
            backstory=self.dimension_info.get("prompt", ""),
            verbose=True,
            llm=self.llm,
        )

    def get_agent(self) -> Agent:
        """Get the underlying CrewAI Agent."""
        return self.agent

    def build_review_prompt(self, prd_content: str) -> str:
        """Build the review prompt for this dimension."""
        return REVIEWER_BASE_PROMPT.format(
            context=prd_content,
            dimension=self.dimension_info.get("name", self.dimension),
        )

    def parse_result(self, result: str) -> Dict[str, Any]:
        """Parse the review result from LLM output."""
        try:
            # Extract JSON from the result
            if "```json" in result:
                result = result.split("```json")[1].split("```")[0]
            elif "```" in result:
                result = result.split("```")[1].split("```")[0]

            return json.loads(result.strip())
        except json.JSONDecodeError:
            return {
                "dimension": self.dimension,
                "score": 0.0,
                "issues": [],
                "reasoning": f"解析失败: {result[:200]}",
            }


class CompletenessReviewer(DimensionReviewer):
    """Reviewer for requirement completeness."""

    def __init__(self, **kwargs):
        super().__init__(dimension="completeness", **kwargs)


class ReasonablenessReviewer(DimensionReviewer):
    """Reviewer for requirement reasonableness."""

    def __init__(self, **kwargs):
        super().__init__(dimension="reasonableness", **kwargs)


class UserValueReviewer(DimensionReviewer):
    """Reviewer for user value."""

    def __init__(self, **kwargs):
        super().__init__(dimension="user_value", **kwargs)


class FeasibilityReviewer(DimensionReviewer):
    """Reviewer for technical feasibility."""

    def __init__(self, **kwargs):
        super().__init__(dimension="feasibility", **kwargs)


class RiskReviewer(DimensionReviewer):
    """Reviewer for implementation risk."""

    def __init__(self, **kwargs):
        super().__init__(dimension="risk", **kwargs)


class PriorityConsistencyReviewer(DimensionReviewer):
    """Reviewer for priority consistency."""

    def __init__(self, **kwargs):
        super().__init__(dimension="priority_consistency", **kwargs)


def get_all_reviewers(
    model: str = "MiniMax-M2.7",
    api_key: Optional[str] = None,
    api_base: Optional[str] = None,
) -> Dict[str, DimensionReviewer]:
    """Get all dimension reviewers."""
    common_kwargs = {"model": model, "api_key": api_key, "api_base": api_base}

    return {
        "completeness": CompletenessReviewer(**common_kwargs),
        "reasonableness": ReasonablenessReviewer(**common_kwargs),
        "user_value": UserValueReviewer(**common_kwargs),
        "feasibility": FeasibilityReviewer(**common_kwargs),
        "risk": RiskReviewer(**common_kwargs),
        "priority_consistency": PriorityConsistencyReviewer(**common_kwargs),
    }
