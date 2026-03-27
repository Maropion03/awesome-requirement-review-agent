"""PRD Reviewer Agent - A multi-dimensional PRD review system."""

from .models import (
    Severity,
    Recommendation,
    Dimension,
    PRDDocument,
    PRDSection,
    Issue,
    DimensionResult,
    ReviewResult,
    AggregatedResult,
)

from .config import get_preset, get_verdict_thresholds, WeightPreset, get_issue_rules

from .parser import PRDParser, parse_prd

from .reviewers import DimensionReviewer, review_prd

from .aggregator import IssueAggregator, aggregate_issues

from .reporter import ReportGenerator, generate_report, ReviewReport


__all__ = [
    # Models
    "Severity",
    "Recommendation",
    "Dimension",
    "PRDDocument",
    "PRDSection",
    "Issue",
    "DimensionResult",
    "ReviewResult",
    "AggregatedResult",
    # Config
    "get_preset",
    "get_verdict_thresholds",
    "WeightPreset",
    "get_issue_rules",
    # Parser
    "PRDParser",
    "parse_prd",
    # Reviewers
    "DimensionReviewer",
    "review_prd",
    # Aggregator
    "IssueAggregator",
    "aggregate_issues",
    # Reporter
    "ReportGenerator",
    "generate_report",
    "ReviewReport",
]
