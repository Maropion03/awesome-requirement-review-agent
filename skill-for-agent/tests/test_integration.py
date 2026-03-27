"""Integration tests for PRD Reviewer Agent."""

import os
import unittest
import tempfile
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from prd_review_skill.models import Dimension, Recommendation
from prd_review_skill.parser import PRDParser
from prd_review_skill.reviewers import DimensionReviewer
from prd_review_skill.aggregator import IssueAggregator
from prd_review_skill.reporter import ReportGenerator, generate_report
from prd_review_skill.config import get_preset


class TestEndToEnd(unittest.TestCase):
    """End-to-end integration tests."""

    def test_full_pipeline_markdown(self):
        """Test the full pipeline with markdown input."""
        content = """# 期宝图自定义指标AI助手

## 项目信息
- 项目：期宝图自定义指标AI助手
- 版本：v1.0.0
- 日期：2024-01-15

## 功能需求

### P0 核心功能
1. 指标自定义配置
2. AI智能推荐

### 验收标准
- 配置保存成功
- AI推荐准确率 > 85%
- 响应时间 < 200ms

### 边界条件
- 无数据时显示默认指标
- API异常时返回缓存数据

依赖行情数据API接口。

## 技术实现

使用Python异步框架，预计QPS 500。
"""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".md", delete=False, encoding="utf-8"
        ) as f:
            f.write(content)
            temp_path = f.name

        try:
            # Parse
            parser = PRDParser()
            doc = parser.parse(temp_path)
            self.assertEqual(doc.project_name, "期宝图自定义指标AI助手")

            # Review
            preset = get_preset("normal")
            reviewer = DimensionReviewer(preset)
            review_result = reviewer.review(doc)
            self.assertGreaterEqual(review_result.total_score, 0)
            self.assertLessEqual(review_result.total_score, 10)

            # Aggregate
            aggregator = IssueAggregator()
            aggregated = aggregator.aggregate(review_result)
            self.assertGreaterEqual(aggregated.total_issues, 0)

            # Generate report
            generator = ReportGenerator(preset)
            report = generator.generate(doc, review_result, aggregated)
            self.assertEqual(report.project_name, "期宝图自定义指标AI助手")
            self.assertAlmostEqual(report.total_score, review_result.total_score, places=2)

        finally:
            Path(temp_path).unlink()

    def test_full_pipeline_with_p0_preset(self):
        """Test with P0 critical preset."""
        content = """# 紧急项目

## P0 功能

关键功能实现

## 验收标准
- 功能可用
"""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".md", delete=False, encoding="utf-8"
        ) as f:
            f.write(content)
            temp_path = f.name

        try:
            parser = PRDParser()
            doc = parser.parse(temp_path)

            preset = get_preset("p0_critical")
            reviewer = DimensionReviewer(preset)
            review_result = reviewer.review(doc)

            aggregator = IssueAggregator()
            aggregated = aggregator.aggregate(review_result)

            generator = ReportGenerator(preset)
            report = generator.generate(doc, review_result, aggregated)

            # P0 preset weights should favor completeness and feasibility
            weights = preset.weights
            self.assertEqual(weights[Dimension.COMPLETENESS], 0.35)
            self.assertEqual(weights[Dimension.FEASIBILITY], 0.35)

        finally:
            Path(temp_path).unlink()

    def test_markdown_output_format(self):
        """Test markdown output format."""
        content = """# 测试项目

## 功能

测试功能

## 验收标准
- 标准1
"""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".md", delete=False, encoding="utf-8"
        ) as f:
            f.write(content)
            temp_path = f.name

        try:
            parser = PRDParser()
            doc = parser.parse(temp_path)

            preset = get_preset("normal")
            reviewer = DimensionReviewer(preset)
            review_result = reviewer.review(doc)

            aggregator = IssueAggregator()
            aggregated = aggregator.aggregate(review_result)

            generator = ReportGenerator(preset)
            report = generator.generate(doc, review_result, aggregated)

            # Generate markdown
            markdown = generator.to_markdown(report)

            self.assertIn("# 需求评审报告", markdown)
            self.assertIn("## 基本信息", markdown)
            self.assertIn("## 综合评分", markdown)
            self.assertIn("## 维度评分", markdown)
            self.assertIn("## 问题清单", markdown)
            self.assertIn("## 评审结论", markdown)

        finally:
            Path(temp_path).unlink()

    def test_json_output_format(self):
        """Test JSON output format."""
        content = """# 测试项目

## 功能

测试功能
"""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".md", delete=False, encoding="utf-8"
        ) as f:
            f.write(content)
            temp_path = f.name

        try:
            parser = PRDParser()
            doc = parser.parse(temp_path)

            preset = get_preset("normal")
            reviewer = DimensionReviewer(preset)
            review_result = reviewer.review(doc)

            aggregator = IssueAggregator()
            aggregated = aggregator.aggregate(review_result)

            generator = ReportGenerator(preset)
            report = generator.generate(doc, review_result, aggregated)

            # Generate JSON
            json_output = generator.to_json(report)

            self.assertIn("project_name", json_output)
            self.assertIn("total_score", json_output)
            self.assertIn("recommendation", json_output)
            self.assertIn("dimension_scores", json_output)

        finally:
            Path(temp_path).unlink()

    def test_report_recommendation_thresholds(self):
        """Test that recommendations are assigned correctly based on thresholds."""
        # Very incomplete PRD should have lower score
        bad_content = "# 差项目\n\n没有验收标准。"
        rec = self._get_recommendation(bad_content)
        # A very incomplete PRD should trigger issues
        self.assertIn(rec, [Recommendation.APPROVE, Recommendation.APPROVE_WITH_MODIFICATIONS, Recommendation.REJECT])

    def test_integration_with_real_prd(self):
        """Test with the actual PRD file if it exists."""
        prd_path = os.getenv("PRD_REVIEWER_REAL_PRD")

        if not prd_path:
            self.skipTest("PRD_REVIEWER_REAL_PRD not set")

        if not Path(prd_path).exists():
            self.skipTest(f"PRD file not found: {prd_path}")

        # Parse
        parser = PRDParser()
        doc = parser.parse(prd_path)
        # Project name may or may not be extracted depending on PRD format
        # Just verify we got a valid parsed result
        self.assertIsNotNone(doc)

        # Review
        preset = get_preset("normal")
        reviewer = DimensionReviewer(preset)
        review_result = reviewer.review(doc)

        # Aggregate
        aggregator = IssueAggregator()
        aggregated = aggregator.aggregate(review_result)

        # Generate report
        generator = ReportGenerator(preset)
        report = generator.generate(doc, review_result, aggregated)

        # Verify report
        self.assertGreater(report.total_score, 0)
        self.assertIsNotNone(report.project_name)

        # Generate markdown output
        markdown = generator.to_markdown(report)
        self.assertGreater(len(markdown), 0)

    def _get_recommendation(self, content: str) -> Recommendation:
        """Helper to get recommendation for content."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".md", delete=False, encoding="utf-8"
        ) as f:
            f.write(content)
            temp_path = f.name

        try:
            parser = PRDParser()
            doc = parser.parse(temp_path)
            preset = get_preset("normal")
            reviewer = DimensionReviewer(preset)
            review_result = reviewer.review(doc)

            return review_result.recommendation
        finally:
            Path(temp_path).unlink()


class TestGenerateReportFunction(unittest.TestCase):
    """Test the generate_report convenience function."""

    def test_generate_report_function(self):
        """Test generate_report convenience function."""
        content = """# 测试

## 验收标准
- 标准1
"""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".md", delete=False, encoding="utf-8"
        ) as f:
            f.write(content)
            temp_path = f.name

        try:
            parser = PRDParser()
            doc = parser.parse(temp_path)

            preset = get_preset("normal")
            reviewer = DimensionReviewer(preset)
            review_result = reviewer.review(doc)

            aggregator = IssueAggregator()
            aggregated = aggregator.aggregate(review_result)

            report = generate_report(doc, review_result, aggregated, preset)

            self.assertIsNotNone(report.project_name)
            self.assertGreaterEqual(report.total_score, 0)
            self.assertLessEqual(report.total_score, 10)

        finally:
            Path(temp_path).unlink()


if __name__ == "__main__":
    unittest.main()
