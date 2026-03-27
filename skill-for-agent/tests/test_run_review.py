import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "run_review.py"


class TestRunReviewScript(unittest.TestCase):
    def test_markdown_path_outputs_markdown_report(self):
        prd = """# 测试项目

## 项目信息
- 项目：测试项目
- 版本：v1.0.0

## 功能需求
需要支持文档评审。
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            prd_path = Path(tmpdir) / "sample.md"
            prd_path.write_text(prd, encoding="utf-8")

            result = subprocess.run(
                [sys.executable, str(SCRIPT), str(prd_path), "--format", "markdown"],
                capture_output=True,
                text=True,
            )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("# 需求评审报告", result.stdout)
        self.assertIn("## 维度评分", result.stdout)
        self.assertIn("需求完整性", result.stdout)
        self.assertIn("需求合理性", result.stdout)
        self.assertIn("用户价值", result.stdout)
        self.assertIn("技术可行性", result.stdout)
        self.assertIn("实现风险", result.stdout)
        self.assertIn("优先级一致性", result.stdout)
        self.assertIn("验收标准缺失", result.stdout)
        self.assertIn("工期估算缺失", result.stdout)
        self.assertIn("建议：✅ 通过", result.stdout)

    def test_unsupported_extension_returns_error(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            prd_path = Path(tmpdir) / "sample.txt"
            prd_path.write_text("not supported", encoding="utf-8")

            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    str(prd_path),
                ],
                capture_output=True,
                text=True,
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Unsupported file type", result.stderr)

    def test_directory_path_returns_error(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            prd_path = Path(tmpdir) / "sample.md"
            prd_path.mkdir()

            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    str(prd_path),
                ],
                capture_output=True,
                text=True,
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Not a file", result.stderr)


if __name__ == "__main__":
    unittest.main()
