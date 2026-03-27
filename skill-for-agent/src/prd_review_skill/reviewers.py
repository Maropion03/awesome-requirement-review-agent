"""Dimension Reviewers Module.

Performs 6-dimension review of the parsed PRD.
"""

import re
from abc import ABC, abstractmethod
from typing import List, Dict, Any
from concurrent.futures import ThreadPoolExecutor, as_completed

from .models import (
    PRDDocument,
    Issue,
    DimensionResult,
    ReviewResult,
    Dimension,
    Severity,
    Recommendation,
)
from .config import WeightPreset, get_verdict_thresholds


class BaseReviewer(ABC):
    """Abstract base class for dimension reviewers."""

    # Shared issue counter across all reviewers
    _issue_counter = {"HIGH": 0, "MEDIUM": 0, "LOW": 0}

    def __init__(self, preset: WeightPreset):
        self.preset = preset
        self.weights = preset.weights

    @property
    @abstractmethod
    def dimension(self) -> Dimension:
        """Return the dimension this reviewer handles."""
        pass

    @abstractmethod
    def review(self, doc: PRDDocument) -> List[Issue]:
        """Review the document and return issues found."""
        pass

    def _next_issue_id(self, severity: Severity) -> str:
        """Generate next issue ID."""
        key = severity.name
        self._issue_counter[key] += 1
        return f"[{severity.value[0]}-{self._issue_counter[key]}]"

    def _create_issue(
        self,
        severity: Severity,
        title: str,
        location: str,
        description: str,
        suggestion: str,
        section: str = "全局",
    ) -> Issue:
        """Create an issue."""
        return Issue(
            id=self._next_issue_id(severity),
            severity=severity,
            title=title,
            location=location,
            description=description,
            suggestion=suggestion,
            section=section,
            dimension=self.dimension,
        )

    def _calculate_score(self, issues: List[Issue]) -> float:
        """Calculate dimension score based on issues."""
        base_score = 10.0
        penalties = {Severity.HIGH: 3.0, Severity.MEDIUM: 1.5, Severity.LOW: 0.5}

        for issue in issues:
            penalty = penalties.get(issue.severity, 0.5)
            base_score -= penalty

        return max(0.0, min(10.0, base_score))


class CompletenessReviewer(BaseReviewer):
    """Reviews requirement completeness dimension."""

    @property
    def dimension(self) -> Dimension:
        return Dimension.COMPLETENESS

    def review(self, doc: PRDDocument) -> List[Issue]:
        issues = []
        raw = doc.raw_text.lower()

        has_acceptance = bool(re.search(r"验收|acceptance|criteria|验收标准", raw))
        if not has_acceptance:
            issues.append(self._create_issue(
                Severity.HIGH,
                "验收标准缺失",
                "文档全局",
                "PRD中未找到明确的验收标准或验收条件定义",
                "为每个功能模块添加清晰的验收条件，说明功能完成的标准",
            ))

        has_boundary = bool(re.search(r"边界|异常|否则|错误处理", raw))
        if not has_boundary:
            issues.append(self._create_issue(
                Severity.MEDIUM,
                "边界条件未定义",
                "文档全局",
                "PRD中未找到对边界条件或异常情况的处理说明",
                "为关键功能添加边界条件和异常处理说明",
            ))

        has_specific_values = bool(re.search(r"\d+[%℃个亿万元]", raw))
        if not has_specific_values:
            issues.append(self._create_issue(
                Severity.MEDIUM,
                "功能描述模糊",
                "文档全局",
                "PRD中缺少具体数值或明确的行为定义",
                "为功能需求添加具体的数值指标和明确的行为定义",
            ))

        return issues


class ReasonablenessReviewer(BaseReviewer):
    """Reviews requirement reasonableness dimension."""

    @property
    def dimension(self) -> Dimension:
        return Dimension.REASONABLENESS

    def review(self, doc: PRDDocument) -> List[Issue]:
        issues = []
        raw = doc.raw_text

        over_design_patterns = [
            (r"未来|以后可能会|预留.*接口", "可能存在过度设计"),
            (r"一切|所有|全部", "使用了绝对化表述，可能导致过度设计"),
        ]

        for pattern, title in over_design_patterns:
            if re.search(pattern, raw):
                issues.append(self._create_issue(
                    Severity.MEDIUM,
                    title,
                    "文档全局",
                    f"发现可能存在过度设计的描述",
                    "聚焦当前版本需求，避免为未来可能不需要的功能预留设计",
                ))

        ambiguous_words = [r"大概|可能|也许|似乎", r"参考.*文档", r"类似.*功能"]
        for pattern in ambiguous_words:
            if re.search(pattern, raw):
                issues.append(self._create_issue(
                    Severity.LOW,
                    "术语不一致",
                    "文档全局",
                    "同一概念有多种表述方式",
                    "统一术语使用，保持表述一致性",
                ))
                break

        return issues


class UserValueReviewer(BaseReviewer):
    """Reviews user value dimension."""

    @property
    def dimension(self) -> Dimension:
        return Dimension.USER_VALUE

    def review(self, doc: PRDDocument) -> List[Issue]:
        issues = []
        raw = doc.raw_text

        has_persona = bool(re.search(r"用户|角色|persona|受众", raw))
        has_problem = bool(re.search(r"痛点|问题|需求|场景", raw))
        has_solution = bool(re.search(r"方案|功能|产品|实现", raw))

        if not (has_persona and has_problem and has_solution):
            issues.append(self._create_issue(
                Severity.MEDIUM,
                "场景-痛点-方案不完整",
                "文档全局",
                "PRD中缺少用户场景、痛点或解决方案的完整描述",
                "确保每个功能都有对应的用户场景、痛点和解决方案说明",
            ))

        has_value_proposition = bool(re.search(r"价值|收益|好处|提升|增加|减少", raw))
        if not has_value_proposition:
            issues.append(self._create_issue(
                Severity.MEDIUM,
                "用户价值不明确",
                "文档全局",
                "PRD中缺少对用户价值的清晰说明",
                "明确说明每个功能对用户的价值和收益",
            ))

        return issues


class FeasibilityReviewer(BaseReviewer):
    """Reviews technical feasibility dimension."""

    @property
    def dimension(self) -> Dimension:
        return Dimension.FEASIBILITY

    def review(self, doc: PRDDocument) -> List[Issue]:
        issues = []
        raw = doc.raw_text.lower()

        dep_keywords = ["依赖", "第三方", "接口", "API", "service", "外部系统", "platform", "SDK"]
        has_dep = any(kw in raw for kw in dep_keywords)

        if has_dep:
            dep_explained = bool(re.search(r"依赖.*说明|接口.*规范|API.*文档", raw))
            if not dep_explained:
                issues.append(self._create_issue(
                    Severity.MEDIUM,
                    "技术依赖未标注",
                    "文档全局",
                    "PRD中引用了外部系统或接口但未提供详细说明",
                    "为所有技术依赖提供详细的接口规范或引用说明",
                ))

        has_perf = bool(re.search(r"性能|响应|延迟|QPS|TPS|并发", raw))
        if not has_perf and len(doc.raw_text) > 1000:
            issues.append(self._create_issue(
                Severity.LOW,
                "性能要求未定义",
                "文档全局",
                "PRD中未找到性能相关的要求定义",
                "为关键功能添加性能指标要求",
            ))

        return issues


class RiskReviewer(BaseReviewer):
    """Reviews implementation risk dimension."""

    @property
    def dimension(self) -> Dimension:
        return Dimension.RISK

    def review(self, doc: PRDDocument) -> List[Issue]:
        issues = []
        raw = doc.raw_text

        complexity_keywords = [r"复杂", r"高并发", r"大数据", r"实时", r"异步", r"分布式", r"事务", r"锁"]
        complexity_count = sum(1 for kw in complexity_keywords if re.search(kw, raw))

        if complexity_count > 3:
            issues.append(self._create_issue(
                Severity.MEDIUM,
                "实现复杂度较高",
                "文档全局",
                f"PRD涉及多个复杂技术点（{complexity_count}个），实现风险较高",
                "考虑将复杂功能拆分为多个小功能逐步实现",
            ))

        has_timeline = bool(re.search(r"工期|时间|deadline|里程碑", raw))
        if not has_timeline:
            issues.append(self._create_issue(
                Severity.LOW,
                "工期估算缺失",
                "文档全局",
                "PRD中未找到工期估算或里程碑定义",
                "为项目添加工期估算和关键里程碑",
            ))

        return issues


class PriorityConsistencyReviewer(BaseReviewer):
    """Reviews priority consistency dimension."""

    @property
    def dimension(self) -> Dimension:
        return Dimension.PRIORITY_CONSISTENCY

    def review(self, doc: PRDDocument) -> List[Issue]:
        issues = []
        raw = doc.raw_text

        high_priority_sections = re.findall(r"(P0|P1)[^P]*", raw)

        if high_priority_sections:
            has_value_mention = bool(re.search(r"价值|收益|核心|关键", raw))
            if not has_value_mention:
                issues.append(self._create_issue(
                    Severity.MEDIUM,
                    "优先级与价值不匹配",
                    "文档全局",
                    "存在高优先级功能但未明确说明其价值",
                    "为P0/P1功能明确说明其业务价值和优先级依据",
                ))

        return issues


class DimensionReviewer:
    """Orchestrates review across all 6 dimensions."""

    def __init__(self, preset: WeightPreset):
        self.preset = preset
        self._reviewers: Dict[Dimension, BaseReviewer] = {
            Dimension.COMPLETENESS: CompletenessReviewer(preset),
            Dimension.REASONABLENESS: ReasonablenessReviewer(preset),
            Dimension.USER_VALUE: UserValueReviewer(preset),
            Dimension.FEASIBILITY: FeasibilityReviewer(preset),
            Dimension.RISK: RiskReviewer(preset),
            Dimension.PRIORITY_CONSISTENCY: PriorityConsistencyReviewer(preset),
        }

    def review(self, doc: PRDDocument) -> ReviewResult:
        """Perform full review of the PRD."""
        with ThreadPoolExecutor(max_workers=6) as executor:
            futures = {
                executor.submit(r.review, doc): dim
                for dim, r in self._reviewers.items()
            }

            dimension_results = []
            for future in as_completed(futures):
                reviewer = self._reviewers[futures[future]]
                issues = future.result()
                score = reviewer._calculate_score(issues)
                weight = self.preset.weights[reviewer.dimension]

                dimension_results.append(DimensionResult(
                    dimension=reviewer.dimension,
                    score=score,
                    weight=weight,
                    weighted_score=score * weight,
                    issue_count=len(issues),
                    issues=issues,
                ))

        dimension_results.sort(key=lambda r: list(Dimension).index(r.dimension))

        total_score = sum(r.weighted_score for r in dimension_results)
        recommendation = self._determine_recommendation(total_score)

        return ReviewResult(
            dimension_results=dimension_results,
            total_score=total_score,
            recommendation=recommendation,
        )

    def _determine_recommendation(self, total_score: float) -> Recommendation:
        """Determine recommendation based on total score."""
        thresholds = get_verdict_thresholds()
        if total_score >= thresholds["pass"]:
            return Recommendation.APPROVE
        elif total_score >= thresholds["modify"]:
            return Recommendation.APPROVE_WITH_MODIFICATIONS
        else:
            return Recommendation.REJECT


def review_prd(doc: PRDDocument, preset: WeightPreset) -> ReviewResult:
    """Convenience function to review a parsed PRD."""
    reviewer = DimensionReviewer(preset)
    return reviewer.review(doc)
