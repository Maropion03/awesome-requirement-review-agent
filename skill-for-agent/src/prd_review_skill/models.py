"""Core data models for PRD Reviewer."""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Dict, Any


class Severity(Enum):
    """Issue severity level."""
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"

    @property
    def display(self) -> str:
        displays = {
            Severity.HIGH: "🔴 高",
            Severity.MEDIUM: "🟡 中",
            Severity.LOW: "🟢 低",
        }
        return displays[self]


class Recommendation(Enum):
    """Review recommendation verdict."""
    APPROVE = "APPROVE"
    APPROVE_WITH_MODIFICATIONS = "APPROVE_WITH_MODIFICATIONS"
    REJECT = "REJECT"

    @property
    def display(self) -> str:
        displays = {
            Recommendation.APPROVE: "✅ 通过",
            Recommendation.APPROVE_WITH_MODIFICATIONS: "⚠️ 修改后通过",
            Recommendation.REJECT: "❌ 驳回",
        }
        return displays[self]


class Dimension(Enum):
    """Review dimension."""
    COMPLETENESS = "需求完整性"
    REASONABLENESS = "需求合理性"
    USER_VALUE = "用户价值"
    FEASIBILITY = "技术可行性"
    RISK = "实现风险"
    PRIORITY_CONSISTENCY = "优先级一致性"


@dataclass
class PRDSection:
    """Represents a section in the PRD."""
    title: str
    level: int
    content: str
    line_number: int
    children: List["PRDSection"] = field(default_factory=list)


@dataclass
class PRDDocument:
    """Parsed PRD document structure."""
    project_name: str
    version: str
    date: Optional[str]
    author: Optional[str]
    sections: List[PRDSection]
    raw_text: str
    file_format: str  # "markdown" or "docx"


@dataclass
class Issue:
    """A found issue in the PRD."""
    id: str
    severity: Severity
    title: str
    location: str
    description: str
    suggestion: str
    section: str
    dimension: Dimension

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "severity": self.severity.value,
            "severity_display": self.severity.display,
            "title": self.title,
            "location": self.location,
            "description": self.description,
            "suggestion": self.suggestion,
            "section": self.section,
            "dimension": self.dimension.value,
        }


@dataclass
class DimensionResult:
    """Result of reviewing a single dimension."""
    dimension: Dimension
    score: float  # 0-10
    weight: float  # 0-1
    weighted_score: float  # score * weight
    issue_count: int
    issues: List[Issue]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "dimension": self.dimension.value,
            "score": round(self.score, 2),
            "weight": self.weight,
            "weighted_score": round(self.weighted_score, 2),
            "issue_count": self.issue_count,
            "issues": [i.to_dict() for i in self.issues],
        }


@dataclass
class ReviewResult:
    """Complete review result for all dimensions."""
    dimension_results: List[DimensionResult]
    total_score: float
    recommendation: Recommendation

    def get_all_issues(self) -> List[Issue]:
        """Get all issues from all dimensions."""
        all_issues = []
        for result in self.dimension_results:
            all_issues.extend(result.issues)
        return all_issues

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_score": round(self.total_score, 2),
            "recommendation": self.recommendation.value,
            "recommendation_display": self.recommendation.display,
            "dimension_results": [r.to_dict() for r in self.dimension_results],
        }


@dataclass
class AggregatedResult:
    """Aggregated issues organized by severity."""
    high_severity: List[Issue]
    medium_severity: List[Issue]
    low_severity: List[Issue]
    by_section: Dict[str, List[Issue]]
    by_dimension: Dict[str, List[Issue]]
    total_issues: int
    high_count: int
    medium_count: int
    low_count: int
