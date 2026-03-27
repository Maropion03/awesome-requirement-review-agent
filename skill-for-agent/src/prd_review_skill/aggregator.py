"""Issue Aggregator Module.

Aggregates and organizes issues found during review.
"""

from typing import Dict, List
from collections import defaultdict

from .models import Issue, ReviewResult, Severity, AggregatedResult


class IssueAggregator:
    """Aggregates issues from review results."""

    def aggregate(self, review_result: ReviewResult) -> AggregatedResult:
        """Aggregate issues from review result.

        Args:
            review_result: Result from dimension reviewer

        Returns:
            AggregatedResult with issues organized by severity and section
        """
        all_issues = review_result.get_all_issues()

        # Group by severity
        high = [i for i in all_issues if i.severity == Severity.HIGH]
        medium = [i for i in all_issues if i.severity == Severity.MEDIUM]
        low = [i for i in all_issues if i.severity == Severity.LOW]

        # Group by section
        by_section: Dict[str, List[Issue]] = defaultdict(list)
        for issue in all_issues:
            by_section[issue.section].append(issue)

        # Group by dimension
        by_dimension: Dict[str, List[Issue]] = defaultdict(list)
        for issue in all_issues:
            by_dimension[issue.dimension.value].append(issue)

        # Sort each group by severity then by id
        def sort_key(item: Issue) -> tuple:
            severity_order = {Severity.HIGH: 0, Severity.MEDIUM: 1, Severity.LOW: 2}
            return (severity_order[item.severity], item.id)

        high.sort(key=sort_key)
        medium.sort(key=sort_key)
        low.sort(key=sort_key)

        for section in by_section:
            by_section[section].sort(key=sort_key)
        for dim in by_dimension:
            by_dimension[dim].sort(key=sort_key)

        return AggregatedResult(
            high_severity=high,
            medium_severity=medium,
            low_severity=low,
            by_section=dict(by_section),
            by_dimension=dict(by_dimension),
            total_issues=len(all_issues),
            high_count=len(high),
            medium_count=len(medium),
            low_count=len(low),
        )


def aggregate_issues(review_result: ReviewResult) -> AggregatedResult:
    """Convenience function to aggregate issues."""
    aggregator = IssueAggregator()
    return aggregator.aggregate(review_result)
