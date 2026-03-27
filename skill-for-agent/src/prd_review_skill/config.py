"""Configuration module for PRD Reviewer."""

from dataclasses import dataclass
from typing import Dict

from .models import Dimension


@dataclass
class WeightPreset:
    """Weight preset for review dimensions."""
    name: str
    weights: Dict[Dimension, float]


# Weight presets configuration
PRESETS = {
    "normal": WeightPreset(
        name="常规项目",
        weights={
            Dimension.COMPLETENESS: 0.20,
            Dimension.REASONABLENESS: 0.20,
            Dimension.USER_VALUE: 0.20,
            Dimension.FEASIBILITY: 0.20,
            Dimension.RISK: 0.10,
            Dimension.PRIORITY_CONSISTENCY: 0.10,
        },
    ),
    "p0_critical": WeightPreset(
        name="P0 紧急项目",
        weights={
            Dimension.COMPLETENESS: 0.35,
            Dimension.REASONABLENESS: 0.10,
            Dimension.USER_VALUE: 0.10,
            Dimension.FEASIBILITY: 0.35,
            Dimension.RISK: 0.10,
            Dimension.PRIORITY_CONSISTENCY: 0.10,
        },
    ),
    "innovation": WeightPreset(
        name="创新探索项目",
        weights={
            Dimension.COMPLETENESS: 0.30,
            Dimension.REASONABLENESS: 0.10,
            Dimension.USER_VALUE: 0.40,
            Dimension.FEASIBILITY: 0.10,
            Dimension.RISK: 0.10,
            Dimension.PRIORITY_CONSISTENCY: 0.10,
        },
    ),
}

# Verdict thresholds
VERDICT_THRESHOLDS = {
    "pass": 8.0,
    "modify": 6.0,
}


def get_preset(name: str) -> WeightPreset:
    """Get a weight preset by name."""
    if name not in PRESETS:
        raise ValueError(f"Unknown preset: {name}. Available: {list(PRESETS.keys())}")
    return PRESETS[name]


def get_verdict_thresholds() -> Dict[str, float]:
    """Get verdict threshold configuration."""
    return VERDICT_THRESHOLDS


# Issue detection rules
ISSUE_RULES = [
    {
        "type": "功能描述模糊",
        "check": "缺少具体数值或行为定义",
        "severity": "HIGH",
    },
    {
        "type": "验收标准缺失",
        "check": "功能模块无对应验收条件",
        "severity": "HIGH",
    },
    {
        "type": "边界条件未定义",
        "check": "没有「否则如何」的处理",
        "severity": "MEDIUM",
    },
    {
        "type": "优先级与价值不匹配",
        "check": "P0 功能但价值低",
        "severity": "MEDIUM",
    },
    {
        "type": "技术依赖未标注",
        "check": "引用外部系统但无说明",
        "severity": "MEDIUM",
    },
    {
        "type": "术语不一致",
        "check": "同一概念多种表述",
        "severity": "LOW",
    },
]


def get_issue_rules():
    """Get issue detection rules."""
    return ISSUE_RULES
