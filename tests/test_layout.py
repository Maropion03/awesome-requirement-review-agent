import unittest
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class TestRepoBLayout(unittest.TestCase):
    def run_git(self, *args):
        return subprocess.run(
            ["git", "-C", str(ROOT), *args],
            check=False,
            capture_output=True,
            text=True,
        )

    def assert_tracked(self, relative_path):
        result = self.run_git("ls-files", "--error-unmatch", relative_path)
        self.assertEqual(
            result.returncode,
            0,
            msg=f"expected tracked path: {relative_path}\nstdout={result.stdout}\nstderr={result.stderr}",
        )

    def assert_ignored(self, relative_path):
        result = self.run_git("check-ignore", "-q", relative_path)
        self.assertEqual(
            result.returncode,
            0,
            msg=f"expected ignored path: {relative_path}\nstdout={result.stdout}\nstderr={result.stderr}",
        )

    def assert_not_tracked(self, relative_path):
        result = self.run_git("ls-files", "--error-unmatch", relative_path)
        self.assertNotEqual(
            result.returncode,
            0,
            msg=f"unexpected tracked path: {relative_path}\nstdout={result.stdout}\nstderr={result.stderr}",
        )

    def test_web_repo_has_expected_roots_and_no_forbidden_artifacts(self):
        required_paths = [
            ROOT / ".gitignore",
            ROOT / "README.md",
            ROOT / "backend" / "main.py",
            ROOT / "backend" / ".env.example",
            ROOT / "backend" / "uploads" / ".gitkeep",
            ROOT / "frontend" / "package.json",
            ROOT / "frontend" / "src" / "App.vue",
            ROOT / "docs" / "TECH_DESIGN.md",
            ROOT / "docs" / "FRONTEND_DESIGN.md",
            ROOT / "tests" / "test_layout.py",
        ]
        tracked_roots = [
            ".gitignore",
            "README.md",
            "backend/main.py",
            "backend/.env.example",
            "backend/uploads/.gitkeep",
            "frontend/package.json",
            "frontend/src/App.vue",
            "docs/TECH_DESIGN.md",
            "docs/FRONTEND_DESIGN.md",
            "tests/test_layout.py",
        ]
        forbidden_artifacts = [
            "backend/.env",
            "frontend/node_modules/.package-lock.json",
            "frontend/dist/index.html",
        ]

        for path in required_paths:
            with self.subTest(path=path):
                self.assertTrue(path.exists(), f"expected path to exist: {path}")

        for path in tracked_roots:
            with self.subTest(path=path):
                self.assert_tracked(path)

        for path in forbidden_artifacts:
            with self.subTest(path=path):
                self.assert_not_tracked(path)
                self.assert_ignored(path)


if __name__ == "__main__":
    unittest.main()
