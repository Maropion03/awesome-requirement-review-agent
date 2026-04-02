import sys
import unittest
from pathlib import Path


BACKEND_ROOT = Path(__file__).resolve().parents[1] / "backend"
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from utils.report_utils import build_issue_key, sort_and_renumber_issues


class TestReportUtils(unittest.TestCase):
    def test_build_issue_key_is_stable_for_the_same_issue_content(self):
        issue = {
            "severity": "HIGH",
            "dimension": "需求完整性",
            "title": "缺失功能交互流程的完整描述",
            "description": "未描述主流程与异常分支的交互路径",
            "suggestion": "补充主流程、分支流程、异常状态和跳转关系",
        }

        key_a = build_issue_key(issue)
        key_b = build_issue_key(dict(issue))

        self.assertTrue(key_a.startswith("issue::"))
        self.assertEqual(key_a, key_b)

    def test_sort_and_renumber_issues_builds_evidence(self):
        issues = [
            {
                "severity": "HIGH",
                "dimension": "需求完整性",
                "title": "missing quote",
                "description": "desc",
                "suggestion": "add detail",
                "source_quote": "验收标准：用户提交后显示成功",
                "source_section": "验收标准",
                "source_locator": "issue:quote",
            }
        ]

        normalized = sort_and_renumber_issues(issues)
        evidence = normalized[0]["evidence"]
        self.assertEqual(evidence["source_quote"], "验收标准：用户提交后显示成功")
        self.assertEqual(evidence["source_section"], "验收标准")
        self.assertEqual(evidence["source_locator"], "issue:quote")
        self.assertEqual(evidence["issue_key"], normalized[0]["issue_key"])
        self.assertEqual(evidence["display_id"], normalized[0]["display_id"])


if __name__ == "__main__":
    unittest.main()
