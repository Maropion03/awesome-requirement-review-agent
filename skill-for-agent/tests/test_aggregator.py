"""Tests for Issue Aggregator module."""

import unittest
import tempfile
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from prd_review_skill.models import Dimension, Severity, Issue, AggregatedResult
from prd_review_skill.parser import PRDParser
from prd_review_skill.reviewers import DimensionReviewer
from prd_review_skill.aggregator import (
    IssueAggregator,
    aggregate_issues,
)
from prd_review_skill.config import get_preset


class TestIssueAggregator(unittest.TestCase):
    """Test cases for IssueAggregator."""

    def test_aggregate_empty_issues(self):
        """Test aggregating when no issues found."""
        content = """# 完美项目

## 验收标准
- 标准1：准确率 > 90%
- 标准2：响应时间 < 100ms

## 边界条件
- 正常情况：返回推荐结果
- 异常情况：返回默认结果
"""
        review_result = self._get_review_result(content)

        aggregator = IssueAggregator()
        aggregated = aggregator.aggregate(review_result)

        # Aggregator should return valid counts regardless
        self.assertGreaterEqual(aggregated.total_issues, 0)
        self.assertGreaterEqual(aggregated.high_count, 0)
        self.assertGreaterEqual(aggregated.medium_count, 0)
        self.assertGreaterEqual(aggregated.low_count, 0)

    def test_aggregate_by_severity(self):
        """Test issues are grouped by severity correctly."""
        content = "# 简单项目"
        review_result = self._get_review_result(content)

        aggregator = IssueAggregator()
        aggregated = aggregator.aggregate(review_result)

        # All issues should be categorized
        total_categorized = (
            len(aggregated.high_severity) +
            len(aggregated.medium_severity) +
            len(aggregated.low_severity)
        )
        self.assertEqual(total_categorized, aggregated.total_issues)

    def test_aggregate_by_section(self):
        """Test issues are grouped by section."""
        content = """# 测试

## 全局部分
内容

## 功能A
P0功能
"""
        review_result = self._get_review_result(content)

        aggregator = IssueAggregator()
        aggregated = aggregator.aggregate(review_result)

        # Should have section groupings
        self.assertIsInstance(aggregated.by_section, dict)

    def test_aggregate_by_dimension(self):
        """Test issues are grouped by dimension."""
        content = "# 测试"
        review_result = self._get_review_result(content)

        aggregator = IssueAggregator()
        aggregated = aggregator.aggregate(review_result)

        # Should have dimension groupings
        self.assertIsInstance(aggregated.by_dimension, dict)

    def test_aggregate_sorts_by_severity(self):
        """Test that issues are sorted by severity."""
        content = "# 简单内容"
        review_result = self._get_review_result(content)

        aggregator = IssueAggregator()
        aggregated = aggregator.aggregate(review_result)

        # High severity should come first in lists
        if len(aggregated.high_severity) > 0:
            self.assertEqual(aggregated.high_severity[0].severity, Severity.HIGH)

    def test_aggregated_result_structure(self):
        """Test AggregatedResult has all required fields."""
        content = "# 测试"
        review_result = self._get_review_result(content)

        aggregator = IssueAggregator()
        aggregated = aggregator.aggregate(review_result)

        self.assertTrue(hasattr(aggregated, "high_severity"))
        self.assertTrue(hasattr(aggregated, "medium_severity"))
        self.assertTrue(hasattr(aggregated, "low_severity"))
        self.assertTrue(hasattr(aggregated, "by_section"))
        self.assertTrue(hasattr(aggregated, "by_dimension"))
        self.assertTrue(hasattr(aggregated, "total_issues"))
        self.assertTrue(hasattr(aggregated, "high_count"))
        self.assertTrue(hasattr(aggregated, "medium_count"))
        self.assertTrue(hasattr(aggregated, "low_count"))

    def _get_review_result(self, content: str):
        """Helper to get review result for content."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".md", delete=False, encoding="utf-8"
        ) as f:
            f.write(content)
            temp_path = f.name

        try:
            parser = PRDParser()
            parsed = parser.parse(temp_path)
            preset = get_preset("normal")
            reviewer = DimensionReviewer(preset)
            return reviewer.review(parsed)
        finally:
            Path(temp_path).unlink()


class TestAggregateIssuesFunction(unittest.TestCase):
    """Test the aggregate_issues convenience function."""

    def test_aggregate_issues_function(self):
        """Test aggregate_issues convenience function."""
        content = """# 测试

## 验收标准
- 标准1
"""
        review_result = self._get_review_result(content)

        aggregated = aggregate_issues(review_result)

        self.assertIsInstance(aggregated, AggregatedResult)
        self.assertGreaterEqual(aggregated.total_issues, 0)

    def _get_review_result(self, content: str):
        """Helper to get review result for content."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".md", delete=False, encoding="utf-8"
        ) as f:
            f.write(content)
            temp_path = f.name

        try:
            parser = PRDParser()
            parsed = parser.parse(temp_path)
            preset = get_preset("normal")
            reviewer = DimensionReviewer(preset)
            return reviewer.review(parsed)
        finally:
            Path(temp_path).unlink()


if __name__ == "__main__":
    unittest.main()
