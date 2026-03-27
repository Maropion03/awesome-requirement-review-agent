"""Tests for PRD Parser module."""

import unittest
import tempfile
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from prd_review_skill.parser import (
    PRDParser,
    PRDDocument,
    PRDSection,
    parse_prd,
)


class TestPRDParser(unittest.TestCase):
    """Test cases for PRDParser."""

    def test_parse_simple_markdown(self):
        """Test parsing a simple markdown PRD."""
        content = """# 项目名称

## 1. 功能需求

这是功能需求的内容。

## 2. 验收标准

- 标准1
- 标准2

## 3. 边界条件

异常情况处理。
"""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".md", delete=False, encoding="utf-8"
        ) as f:
            f.write(content)
            temp_path = f.name

        try:
            parser = PRDParser()
            result = parser.parse(temp_path)

            self.assertEqual(result.file_format, "markdown")
            self.assertGreaterEqual(len(result.sections), 2)
            # Sections should contain the heading
            section_titles = [s.title for s in result.sections]
            self.assertTrue(any("项目名称" in t or "功能需求" in t for t in section_titles))
        finally:
            Path(temp_path).unlink()

    def test_extract_metadata(self):
        """Test metadata extraction from PRD header."""
        content = """# 智能推荐系统 PRD

- 项目：智能推荐系统
- 版本：v2.1.0
- 日期：2024-01-15
- 作者：张三

## 功能需求
"""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".md", delete=False, encoding="utf-8"
        ) as f:
            f.write(content)
            temp_path = f.name

        try:
            parser = PRDParser()
            result = parser.parse(temp_path)

            self.assertIn("智能推荐系统", result.project_name)
            self.assertIn("v2.1", result.version)
            self.assertIn("2024", result.date)
        finally:
            Path(temp_path).unlink()

    def test_extract_sections(self):
        """Test section extraction from markdown."""
        content = """# 主标题

## 功能模块

### 子功能

内容
"""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".md", delete=False, encoding="utf-8"
        ) as f:
            f.write(content)
            temp_path = f.name

        try:
            parser = PRDParser()
            result = parser.parse(temp_path)

            self.assertGreaterEqual(len(result.sections), 1)
            # Check hierarchy
            for section in result.sections:
                if section.title == "功能模块":
                    self.assertEqual(section.level, 2)
                    break
        finally:
            Path(temp_path).unlink()

    def test_extract_key_info(self):
        """Test extraction of key information."""
        content = """
# 测试项目

## 功能需求

P0 核心功能

依赖第三方API服务。

## 验收标准

1. 满足性能要求
2. 支持并发
"""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".md", delete=False, encoding="utf-8"
        ) as f:
            f.write(content)
            temp_path = f.name

        try:
            parser = PRDParser()
            parsed = parser.parse(temp_path)
            info = parser.extract_key_info(parsed)

            self.assertGreater(info["sections_count"], 0)
            self.assertTrue(info["has_acceptance_criteria"])
            self.assertGreater(len(info["priorities_found"]), 0)
            self.assertIn("API", info["technical_deps"])
        finally:
            Path(temp_path).unlink()

    def test_parse_unsupported_format(self):
        """Test that unsupported formats raise an error."""
        parser = PRDParser()

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt", delete=False
        ) as f:
            f.write("content")
            temp_path = f.name

        try:
            with self.assertRaises(ValueError) as context:
                parser.parse(temp_path)
            self.assertIn("Unsupported", str(context.exception))
        finally:
            Path(temp_path).unlink()

    def test_parse_empty_document(self):
        """Test parsing an empty document."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".md", delete=False, encoding="utf-8"
        ) as f:
            f.write("")
            temp_path = f.name

        try:
            parser = PRDParser()
            result = parser.parse(temp_path)

            self.assertEqual(result.file_format, "markdown")
            self.assertEqual(len(result.sections), 0)
            self.assertEqual(result.project_name, "未知项目")
        finally:
            Path(temp_path).unlink()


class TestParsePRDFunction(unittest.TestCase):
    """Test the parse_prd convenience function."""

    def test_parse_prd_function(self):
        """Test parse_prd convenience function."""
        content = "# 测试\n\n内容"
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".md", delete=False, encoding="utf-8"
        ) as f:
            f.write(content)
            temp_path = f.name

        try:
            result = parse_prd(temp_path)
            self.assertIsInstance(result, PRDDocument)
            self.assertEqual(result.file_format, "markdown")
        finally:
            Path(temp_path).unlink()


if __name__ == "__main__":
    unittest.main()
