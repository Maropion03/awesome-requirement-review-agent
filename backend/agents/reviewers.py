"""
Review Agents - 6 dimension reviewers.
"""

import asyncio
import json
from typing import Optional, Any, Dict

from crewai import Agent

from utils.minimax_client import get_minimax_client
from config.prompts import DIMENSION_PROMPTS, REVIEWER_BASE_PROMPT


class DimensionReviewer:
    """Base class for dimension reviewers."""

    RETRYABLE_ERROR_MARKERS = (
        "2064",
        "当前服务集群负载较高",
        "服务集群负载较高",
        "please retry later",
        "service busy",
    )
    MAX_RETRY_ATTEMPTS = 2
    RETRY_DELAY_SECONDS = 0.6

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
        base_prompt = REVIEWER_BASE_PROMPT.format(
            context=prd_content,
            dimension=self.dimension_info.get("name", self.dimension),
        )
        dimension_prompt = self.dimension_info.get("prompt", "")
        return f"{base_prompt}\n\n维度检查清单：\n{dimension_prompt}".strip()

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

    async def review(self, prd_content: str) -> Dict[str, Any]:
        """Run the actual LLM-backed review for a dimension."""
        prompt = self.build_review_prompt(prd_content)
        loop = asyncio.get_event_loop()
        last_exc = None

        for attempt in range(1, self.MAX_RETRY_ATTEMPTS + 1):
            try:
                result = await loop.run_in_executor(
                    None,
                    lambda: self.llm.invoke(prompt),
                )
                content = result.content if hasattr(result, "content") else str(result)
                return self.parse_result(content)
            except Exception as exc:
                last_exc = exc
                if not self._is_retryable_model_error(exc) or attempt >= self.MAX_RETRY_ATTEMPTS:
                    raise RuntimeError(self._format_model_error(exc)) from exc
                await asyncio.sleep(self.RETRY_DELAY_SECONDS * attempt)

        raise RuntimeError(self._format_model_error(last_exc or RuntimeError("unknown error")))

    def _format_model_error(self, exc: Exception) -> str:
        message = str(exc)
        lowered = message.lower()

        if "401" in message or "authorized_error" in lowered or "login fail" in lowered or "1004" in message:
            return (
                f"MiniMax 认证失败，维度「{self.dimension_info.get('name', self.dimension)}」评审无法继续。"
                "请检查 MINIMAX_API_KEY 和 MINIMAX_API_BASE。"
            )

        if "timeout" in lowered:
            return f"MiniMax 请求超时，维度「{self.dimension_info.get('name', self.dimension)}」评审暂时无法完成。"

        if self._is_retryable_model_error(exc):
            return (
                f"MiniMax 服务暂时繁忙，维度「{self.dimension_info.get('name', self.dimension)}」评审未完成。"
                "请稍后重试。"
            )

        return f"MiniMax 调用失败，维度「{self.dimension_info.get('name', self.dimension)}」评审异常：{message}"

    def _is_retryable_model_error(self, exc: Exception) -> bool:
        lowered = str(exc).lower()
        return any(marker.lower() in lowered for marker in self.RETRYABLE_ERROR_MARKERS)


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
