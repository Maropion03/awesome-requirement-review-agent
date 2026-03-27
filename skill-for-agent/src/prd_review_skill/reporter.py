"""Report Generator Module.

Generates review reports in various formats (Markdown, JSON).
"""

import json
from dataclasses import dataclass
from typing import List, Dict, Any
from datetime import datetime

from .models import PRDDocument, ReviewResult, AggregatedResult, Issue, Recommendation
from .config import WeightPreset


@dataclass
class ReviewReport:
    """Complete review report."""
    project_name: str
    version: str
    review_date: str
    preset_name: str
    total_score: float
    recommendation: Recommendation
    dimension_scores: List[Dict[str, Any]]
    issues_by_severity: Dict[str, List[Dict[str, Any]]]
    issues_by_section: Dict[str, List[Dict[str, Any]]]
    summary: str


class ReportGenerator:
    """Generates review reports."""

    def __init__(self, preset: WeightPreset):
        self.preset = preset

    def generate(
        self,
        doc: PRDDocument,
        review_result: ReviewResult,
        aggregated: AggregatedResult,
    ) -> ReviewReport:
        """Generate a complete review report."""
        # Build dimension scores table
        dimension_scores = [r.to_dict() for r in review_result.dimension_results]

        # Build issues by severity
        issues_by_severity = {
            "high": [self._issue_to_dict(i) for i in aggregated.high_severity],
            "medium": [self._issue_to_dict(i) for i in aggregated.medium_severity],
            "low": [self._issue_to_dict(i) for i in aggregated.low_severity],
        }

        # Build issues by section
        issues_by_section = {}
        for section, issues in aggregated.by_section.items():
            issues_by_section[section] = [self._issue_to_dict(i) for i in issues]

        # Generate summary
        summary = self._generate_summary(review_result, aggregated)

        return ReviewReport(
            project_name=doc.project_name,
            version=doc.version,
            review_date=datetime.now().strftime("%Y-%m-%d"),
            preset_name=self.preset.name,
            total_score=review_result.total_score,
            recommendation=review_result.recommendation,
            dimension_scores=dimension_scores,
            issues_by_severity=issues_by_severity,
            issues_by_section=issues_by_section,
            summary=summary,
        )

    def _issue_to_dict(self, issue: Issue) -> Dict[str, Any]:
        """Convert issue to dictionary."""
        return issue.to_dict()

    def _generate_summary(
        self,
        review_result: ReviewResult,
        aggregated: AggregatedResult,
    ) -> str:
        """Generate a summary of the review."""
        parts = []
        rec = review_result.recommendation

        if rec == Recommendation.APPROVE:
            parts.append("该PRD文档整体质量良好，可以进入开发阶段。")
        elif rec == Recommendation.APPROVE_WITH_MODIFICATIONS:
            parts.append("该PRD文档存在一些需要优化的问题，建议修改后继续。")
        else:
            parts.append("该PRD文档存在较多问题，需要重新修订。")

        parts.append(f"综合评分为 {review_result.total_score:.1f}/10。")

        if aggregated.high_count > 0:
            parts.append(f"发现 {aggregated.high_count} 个高优先级问题需要立即解决。")
        if aggregated.medium_count > 0:
            parts.append(f"发现 {aggregated.medium_count} 个中优先级问题建议优化。")
        if aggregated.low_count > 0:
            parts.append(f"发现 {aggregated.low_count} 个低优先级问题供参考。")

        return " ".join(parts)

    def to_markdown(self, report: ReviewReport) -> str:
        """Generate Markdown format report."""
        lines = [
            "# 需求评审报告",
            "",
            "## 基本信息",
            f"- 项目：{report.project_name}",
            f"- 版本：{report.version}",
            f"- 评审时间：{report.review_date}",
            f"- 项目类型：{report.preset_name}",
            "",
            "## 综合评分",
            f"总分：{report.total_score}/10",
            f"建议：{report.recommendation.display}",
            "",
            "## 维度评分",
            "| 维度 | 得分 | 权重 | 加权得分 | 问题数 |",
            "|------|------|------|---------|-------|",
        ]

        for dim in report.dimension_scores:
            lines.append(
                f"| {dim['dimension']} | {dim['score']} | {dim['weight']:.2f} | "
                f"{dim['weighted_score']:.2f} | {dim['issue_count']} |"
            )

        lines.append("")
        lines.append("## 问题清单")

        # High severity
        if report.issues_by_severity["high"]:
            lines.append("")
            lines.append("### 🔴 高优先级（必须解决）")
            for issue in report.issues_by_severity["high"]:
                lines.append(f"**{issue['id']}** {issue['title']}")
                lines.append(f"- 位置：{issue['location']}")
                lines.append(f"- 问题：{issue['description']}")
                lines.append(f"- 建议：{issue['suggestion']}")
                lines.append("")

        # Medium severity
        if report.issues_by_severity["medium"]:
            lines.append("")
            lines.append("### 🟡 中优先级（建议优化）")
            for issue in report.issues_by_severity["medium"]:
                lines.append(f"**{issue['id']}** {issue['title']}")
                lines.append(f"- 位置：{issue['location']}")
                lines.append(f"- 问题：{issue['description']}")
                lines.append(f"- 建议：{issue['suggestion']}")
                lines.append("")

        # Low severity
        if report.issues_by_severity["low"]:
            lines.append("")
            lines.append("### 🟢 低优先级")
            for issue in report.issues_by_severity["low"]:
                lines.append(f"**{issue['id']}** {issue['title']}")
                lines.append(f"- 位置：{issue['location']}")
                lines.append(f"- 问题：{issue['description']}")
                lines.append(f"- 建议：{issue['suggestion']}")
                lines.append("")

        lines.append("")
        lines.append("## 评审结论")
        lines.append(f"{report.recommendation.display}：{report.summary}")

        return "\n".join(lines)

    def to_json(self, report: ReviewReport) -> str:
        """Generate JSON format report."""
        data = {
            "project_name": report.project_name,
            "version": report.version,
            "review_date": report.review_date,
            "preset_name": report.preset_name,
            "total_score": report.total_score,
            "recommendation": report.recommendation.value,
            "recommendation_display": report.recommendation.display,
            "dimension_scores": report.dimension_scores,
            "issues_by_severity": report.issues_by_severity,
            "issues_by_section": report.issues_by_section,
            "summary": report.summary,
        }
        return json.dumps(data, ensure_ascii=False, indent=2)


def generate_report(
    doc: PRDDocument,
    review_result: ReviewResult,
    aggregated: AggregatedResult,
    preset: WeightPreset,
) -> ReviewReport:
    """Convenience function to generate a report."""
    generator = ReportGenerator(preset)
    return generator.generate(doc, review_result, aggregated)
