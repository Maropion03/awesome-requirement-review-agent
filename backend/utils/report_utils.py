"""Helpers for shaping aggregated review reports."""

import hashlib
from typing import Any, Dict, List


SEVERITY_ORDER = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
MAX_DIMENSION_SCORE = 10.0
MAX_TOTAL_SCORE = 100.0
PASS_RECOMMENDATION = "通过"
MODIFY_RECOMMENDATION = "修改后通过"
FAIL_RECOMMENDATION = "不通过"


def _normalize_string(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _build_evidence(issue: Dict[str, Any]) -> Dict[str, str]:
    return {
        "issue_key": _normalize_string(issue.get("issue_key")),
        "display_id": _normalize_string(issue.get("display_id")),
        "source_quote": _normalize_string(issue.get("source_quote")),
        "source_section": _normalize_string(issue.get("source_section")),
        "source_locator": _normalize_string(issue.get("source_locator")),
    }


def normalize_dimension_score(score: Any) -> float:
    """Clamp a raw reviewer score into the 0-10 dimension range."""
    try:
        value = float(score)
    except (TypeError, ValueError):
        return 0.0

    if value < 0.0:
        return 0.0
    if value > MAX_DIMENSION_SCORE:
        return MAX_DIMENSION_SCORE
    return value


def calculate_weighted_total_score(
    review_results: Dict[str, Dict[str, Any]],
    preset_config: Dict[str, float],
) -> float:
    """Compute a weighted total score on a 0-100 scale from 0-10 reviewer scores."""
    total_score = 0.0
    weight_sum = 0.0

    for dimension, result in review_results.items():
        weight = preset_config.get(dimension, preset_config.get("others", 0.1))
        total_score += normalize_dimension_score(result.get("score", 0)) * weight
        weight_sum += weight

    if weight_sum <= 0:
        return 0.0

    normalized_total = (total_score / weight_sum) * 10
    return round(min(max(normalized_total, 0.0), MAX_TOTAL_SCORE), 1)


def determine_recommendation(total_score: float) -> str:
    """Map a 0-100 total score to the recommendation labels expected by the UI."""
    if total_score >= 80.0:
        return PASS_RECOMMENDATION
    if total_score >= 60.0:
        return MODIFY_RECOMMENDATION
    return FAIL_RECOMMENDATION


def format_report_summary(total_score: float, recommendation: str, issue_count: int = 0) -> str:
    summary = f"综合评分 {total_score}/100，建议：{recommendation}"
    if issue_count:
        summary += f"，共发现 {issue_count} 个问题。"
    return summary


def build_issue_key(issue: Dict[str, Any]) -> str:
    fingerprint = "|".join(
        str(issue.get(field, "")).strip().lower()
        for field in ("severity", "dimension", "title", "description", "suggestion")
    )
    digest = hashlib.sha1(fingerprint.encode("utf-8")).hexdigest()[:12]
    return f"issue::{digest}"


def sort_and_renumber_issues(issues: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Sort issues by severity and assign globally unique ids per severity."""
    sorted_issues = sorted(
        issues,
        key=lambda item: SEVERITY_ORDER.get(str(item.get("severity", "LOW")).upper(), 3),
    )

    counters: Dict[str, int] = {}
    normalized: List[Dict[str, Any]] = []

    for issue in sorted_issues:
        normalized_issue = dict(issue)
        severity = str(normalized_issue.get("severity", "LOW")).upper()
        prefix = severity if severity in SEVERITY_ORDER else "ISSUE"

        counters[prefix] = counters.get(prefix, 0) + 1
        normalized_issue["severity"] = severity
        normalized_issue["id"] = f"{prefix}-{counters[prefix]}"
        normalized_issue["display_id"] = normalized_issue["id"]
        normalized_issue["issue_key"] = build_issue_key(normalized_issue)
        for field in ("source_quote", "source_section", "source_locator"):
            normalized_issue[field] = _normalize_string(normalized_issue.get(field))
        normalized_issue["evidence"] = _build_evidence(normalized_issue)
        normalized.append(normalized_issue)

    return normalized
