"""Tests for Dimension Reviewer module."""

import unittest
import tempfile
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from prd_review_skill.models import Dimension, Severity, Recommendation, ReviewResult
from prd_review_skill.parser import PRDParser
from prd_review_skill.reviewers import DimensionReviewer, review_prd
from prd_review_skill.config import get_preset


class TestDimensionReviewer(unittest.TestCase):
    """Test cases for DimensionReviewer."""

    def test_review_complete_prd(self):
        """Test reviewing a complete PRD."""
        content = """# 智能推荐系统

## 功能需求

P0 核心推荐功能

### 验收标准
- 推荐准确率 > 90%
- 响应时间 < 100ms

### 边界条件
- 无数据时显示默认推荐
- 异常情况返回兜底结果

依赖外部数据API接口。

## 用户价值

解决用户发现感兴趣内容的痛点。

## 技术说明

使用协同过滤算法，预计QPS 1000。
"""
        parsed = self._parse_content(content)
        preset = get_preset("normal")

        reviewer = DimensionReviewer(preset)
        result = reviewer.review(parsed)

        self.assertIsInstance(result, ReviewResult)
        self.assertGreaterEqual(result.total_score, 0)
        self.assertLessEqual(result.total_score, 10)
        self.assertIn(result.recommendation, [Recommendation.APPROVE, Recommendation.APPROVE_WITH_MODIFICATIONS, Recommendation.REJECT])
        self.assertEqual(len(result.dimension_results), 6)

    def test_review_incomplete_prd(self):
        """Test reviewing an incomplete PRD."""
        content = """# 测试项目

这是一个非常简单的PRD，没有验收标准。
"""
        parsed = self._parse_content(content)
        preset = get_preset("normal")

        reviewer = DimensionReviewer(preset)
        result = reviewer.review(parsed)

        # Should have issues found
        all_issues = result.get_all_issues()
        self.assertGreater(len(all_issues), 0)

    def test_completeness_dimension(self):
        """Test completeness dimension scoring."""
        # PRD without acceptance criteria
        content1 = "# 测试\n\n没有验收标准。"
        parsed1 = self._parse_content(content1)

        # PRD with acceptance criteria
        content2 = """# 测试

## 验收标准
- 条件1
- 条件2
"""
        parsed2 = self._parse_content(content2)

        preset = get_preset("normal")
        reviewer = DimensionReviewer(preset)

        result1 = reviewer.review(parsed1)
        result2 = reviewer.review(parsed2)

        completeness1 = next(
            r for r in result1.dimension_results
            if r.dimension == Dimension.COMPLETENESS
        )
        completeness2 = next(
            r for r in result2.dimension_results
            if r.dimension == Dimension.COMPLETENESS
        )

        # Complete PRD should score higher
        self.assertGreaterEqual(completeness2.score, completeness1.score)

    def test_priority_consistency(self):
        """Test priority consistency dimension."""
        content = """# 测试

## P0 核心功能

这是优先级最高的功能。

## 验收标准
- 满足核心价值
"""
        parsed = self._parse_content(content)
        preset = get_preset("normal")

        reviewer = DimensionReviewer(preset)
        result = reviewer.review(parsed)

        pc_result = next(
            r for r in result.dimension_results
            if r.dimension == Dimension.PRIORITY_CONSISTENCY
        )

        self.assertEqual(pc_result.dimension, Dimension.PRIORITY_CONSISTENCY)
        self.assertGreaterEqual(pc_result.score, 0)
        self.assertLessEqual(pc_result.score, 10)

    def test_feasibility_with_deps(self):
        """Test feasibility review with dependencies."""
        content = """# 测试

## 功能需求

依赖外部支付SDK。

## 技术要求

性能要求：QPS > 5000
"""
        parsed = self._parse_content(content)
        preset = get_preset("normal")

        reviewer = DimensionReviewer(preset)
        result = reviewer.review(parsed)

        feas_result = next(
            r for r in result.dimension_results
            if r.dimension == Dimension.FEASIBILITY
        )

        self.assertGreaterEqual(feas_result.issue_count, 0)

    def test_risk_dimension(self):
        """Test risk dimension review."""
        content = """# 测试

涉及高并发、分布式、实时数据处理等复杂技术点。

## 工期

预计2个月完成。
"""
        parsed = self._parse_content(content)
        preset = get_preset("normal")

        reviewer = DimensionReviewer(preset)
        result = reviewer.review(parsed)

        risk_result = next(
            r for r in result.dimension_results
            if r.dimension == Dimension.RISK
        )

        self.assertEqual(risk_result.dimension, Dimension.RISK)
        self.assertGreaterEqual(risk_result.issue_count, 0)

    def test_all_dimensions_scored(self):
        """Test that all 6 dimensions are scored."""
        content = """# 测试项目

简单内容
"""
        parsed = self._parse_content(content)
        preset = get_preset("normal")

        reviewer = DimensionReviewer(preset)
        result = reviewer.review(parsed)

        dimensions_found = {r.dimension for r in result.dimension_results}
        expected_dimensions = {
            Dimension.COMPLETENESS,
            Dimension.REASONABLENESS,
            Dimension.USER_VALUE,
            Dimension.FEASIBILITY,
            Dimension.RISK,
            Dimension.PRIORITY_CONSISTENCY,
        }

        self.assertEqual(dimensions_found, expected_dimensions)

    def test_issue_id_generation(self):
        """Test that issue IDs are generated correctly."""
        content = "# 测试\n\n没有验收标准。边界条件也缺失。"
        parsed = self._parse_content(content)
        preset = get_preset("normal")

        reviewer = DimensionReviewer(preset)
        result = reviewer.review(parsed)

        all_issues = result.get_all_issues()
        for issue in all_issues:
            self.assertTrue(issue.id.startswith("["))
            self.assertIn("]", issue.id)

    def test_weighted_score_calculation(self):
        """Test that weighted total score is calculated correctly."""
        content = "# 测试\n\n内容"
        parsed = self._parse_content(content)
        preset = get_preset("normal")

        reviewer = DimensionReviewer(preset)
        result = reviewer.review(parsed)

        # Calculate expected weighted score
        expected_total = sum(
            r.score * preset.weights[r.dimension]
            for r in result.dimension_results
        )

        self.assertAlmostEqual(result.total_score, expected_total, places=2)

    def _parse_content(self, content: str):
        """Helper to parse content into PRDDocument."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".md", delete=False, encoding="utf-8"
        ) as f:
            f.write(content)
            temp_path = f.name

        try:
            parser = PRDParser()
            return parser.parse(temp_path)
        finally:
            Path(temp_path).unlink()


class TestReviewPRDFunction(unittest.TestCase):
    """Test the review_prd convenience function."""

    def test_review_prd_function(self):
        """Test review_prd convenience function."""
        content = "# 测试\n\n验收标准：功能正常。"
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".md", delete=False, encoding="utf-8"
        ) as f:
            f.write(content)
            temp_path = f.name

        try:
            parser = PRDParser()
            parsed = parser.parse(temp_path)
            preset = get_preset("normal")

            result = review_prd(parsed, preset)

            self.assertIsInstance(result, ReviewResult)
            self.assertGreaterEqual(result.total_score, 0)
            self.assertLessEqual(result.total_score, 10)
        finally:
            Path(temp_path).unlink()


if __name__ == "__main__":
    unittest.main()
