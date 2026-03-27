"""
PRD Validator - validates PRD content against rules.
"""

import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class ValidationIssue:
    """Represents a validation issue."""
    severity: str  # HIGH, MEDIUM, LOW
    title: str
    description: str
    location: Optional[str] = None
    suggestion: Optional[str] = None


class PRDValidator:
    """Validator for PRD content quality."""

    def __init__(self, content: str):
        self.content = content
        self.issues: List[ValidationIssue] = []

    def validate(self) -> Dict[str, Any]:
        """
        Run all validations and return results.

        Returns:
            Dictionary with validation results
        """
        self.issues = []

        self._check_title()
        self._check_version()
        self._check_acceptance_criteria()
        self._check_ambiguous_terms()
        self._check_consistency()
        self._check_completeness()

        return self.get_results()

    def _check_title(self):
        """Check if title exists and is valid."""
        has_heading = bool(re.search(r"^#\s+.+", self.content, re.MULTILINE))
        if not has_heading:
            self.issues.append(ValidationIssue(
                severity="HIGH",
                title="缺少文档标题",
                description="PRD 文档应该以一级标题开始，包含项目或文档名称",
                location="文档开头",
                suggestion="在文档开头添加 # 项目名称 作为标题",
            ))

    def _check_version(self):
        """Check if version information exists."""
        has_version = bool(re.search(
            r"(版本|version|v)\s*[:：]?\s*\d+\.\d+",
            self.content,
            re.IGNORECASE,
        ))
        if not has_version:
            self.issues.append(ValidationIssue(
                severity="MEDIUM",
                title="缺少版本信息",
                description="建议标注当前 PRD 的版本号，便于追踪变更",
                suggestion="添加版本信息，如: 版本 v1.0 或 Version: 1.0",
            ))

    def _check_acceptance_criteria(self):
        """Check if acceptance criteria are defined."""
        has_acceptance = bool(re.search(
            r"(验收标准|验收条件|acceptance criteria|acceptance)",
            self.content,
            re.IGNORECASE,
        ))

        # Check for each major section if it has acceptance criteria
        sections = re.findall(r"^##\s+(.+)$", self.content, re.MULTILINE)

        if not has_acceptance and len(sections) >= 3:
            self.issues.append(ValidationIssue(
                severity="HIGH",
                title="缺少验收标准",
                description="文档中未找到验收标准定义，每个功能需求都应有明确的验收条件",
                suggestion="为每个功能添加验收标准，说明如何判断功能是否完成",
            ))

    def _check_ambiguous_terms(self):
        """Check for ambiguous terms that need clarification."""
        ambiguous_patterns = [
            (r"\b(可能|也许|大概)\b", "模糊的概率表述"),
            (r"\b(优化|提升|改进)\s+(?=[\u4e00-\u9fa5])", "模糊的优化描述"),
            (r"\b(一些|若干|部分)\b", "模糊的数量表述"),
            (r"\b(快速|高效|便捷)\b(?!\s*地)", "模糊的形容词"),
        ]

        for pattern, term_type in ambiguous_patterns:
            matches = re.finditer(pattern, self.content)
            for match in matches:
                self.issues.append(ValidationIssue(
                    severity="MEDIUM",
                    title=f"使用了{term_type}",
                    description=f"在 '{match.group()}' 附近存在不明确的表述",
                    location=f"位置 {match.start()}",
                    suggestion=f"使用更具体的数值或描述替代",
                ))

    def _check_consistency(self):
        """Check for terminology consistency."""
        # Find potential inconsistencies in quoted terms
        quoted_terms = re.findall(r'"([^"]+)"', self.content)

        # Check for similar terms that might be inconsistent
        term_variants = {
            "用户": ["使用者", "客户", "使用者"],
            "功能": ["特性", "能力", "函数"],
            "系统": ["平台"],
        }

        for standard_term, variants in term_variants.items():
            all_terms = [standard_term] + variants
            found_terms = []

            for term in all_terms:
                if term in self.content:
                    found_terms.append(term)

            if len(found_terms) > 1:
                self.issues.append(ValidationIssue(
                    severity="LOW",
                    title="术语不一致",
                    description=f"文档中同时使用了: {', '.join(found_terms)}",
                    suggestion=f"建议统一使用 '{standard_term}'",
                ))

    def _check_completeness(self):
        """Check for completeness issues."""
        lines = self.content.split("\n")

        # Check for empty sections
        section_pattern = r"^##\s+(.+)$"
        current_section = None
        empty_section_count = 0

        for line in lines:
            section_match = re.match(section_pattern, line)
            if section_match:
                if current_section and empty_section_count < 2:
                    self.issues.append(ValidationIssue(
                        severity="MEDIUM",
                        title=f"章节 '{current_section}' 内容过少",
                        description="章节可能缺少必要的详细说明",
                        suggestion="添加详细的功能描述、验收标准等",
                    ))
                current_section = section_match.group(1)
                empty_section_count = 0
            elif line.strip():
                empty_section_count = 0
            else:
                empty_section_count += 1

    def get_results(self) -> Dict[str, Any]:
        """Get validation results."""
        return {
            "is_valid": len([i for i in self.issues if i.severity == "HIGH"]) == 0,
            "total_issues": len(self.issues),
            "issues_by_severity": {
                "HIGH": [i for i in self.issues if i.severity == "HIGH"],
                "MEDIUM": [i for i in self.issues if i.severity == "MEDIUM"],
                "LOW": [i for i in self.issues if i.severity == "LOW"],
            },
            "issues": [
                {
                    "severity": i.severity,
                    "title": i.title,
                    "description": i.description,
                    "location": i.location,
                    "suggestion": i.suggestion,
                }
                for i in self.issues
            ],
        }


def validate_prd(content: str) -> Dict[str, Any]:
    """
    Convenience function to validate PRD content.

    Args:
        content: PRD text content

    Returns:
        Validation results
    """
    validator = PRDValidator(content)
    return validator.validate()
