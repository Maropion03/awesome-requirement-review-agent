import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


BACKEND_ROOT = Path(__file__).resolve().parents[1] / "backend"
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from services.chat_service import build_chat_response


class TestChatService(unittest.TestCase):
    def setUp(self):
        self.original_api_key = os.environ.get("MINIMAX_API_KEY")
        self.original_chat_model = os.environ.get("MINIMAX_CHAT_MODEL")
        os.environ.pop("MINIMAX_API_KEY", None)
        os.environ.pop("MINIMAX_CHAT_MODEL", None)

    def tearDown(self):
        if self.original_api_key is None:
            os.environ.pop("MINIMAX_API_KEY", None)
        else:
            os.environ["MINIMAX_API_KEY"] = self.original_api_key

        if self.original_chat_model is None:
            os.environ.pop("MINIMAX_CHAT_MODEL", None)
        else:
            os.environ["MINIMAX_CHAT_MODEL"] = self.original_chat_model

    def test_build_chat_response_uses_selected_issue_and_run_state(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            prd_path = Path(tmpdir) / "demo.md"
            prd_path.write_text("# Demo\n## 验收标准\n必须支持失败重试。\n", encoding="utf-8")
            session = {
                "status": "completed",
                "preset": "normal",
                "file_path": str(prd_path),
                "progress": 100.0,
                "current_dimension": None,
                "completed_dimensions": ["需求完整性"],
                "report": {
                    "total_score": 76.0,
                    "recommendation": "修改后通过",
                    "summary": "综合评分 76.0/100，建议：修改后通过",
                    "issues": [
                        {
                            "id": "[高-1]",
                            "severity": "HIGH",
                            "title": "验收标准缺失",
                            "dimension": "需求完整性",
                            "description": "缺少失败与异常场景",
                            "suggestion": "补充失败重试说明",
                        }
                    ],
                },
            }

            with patch("services.chat_service.resolve_minimax_config", return_value={
                "model": "MiniMax-M2.7",
                "api_key": None,
                "api_base": "https://api.minimax.chat/v1",
            }):
                result = build_chat_response(
                    session=session,
                    message="为什么这个问题是高优先级？",
                    selected_issue_id="[高-1]",
                    context_mode="default",
                )

            self.assertIn("高优先级", result["message"])
            self.assertEqual(result["target_issue_id"], "[高-1]")
            self.assertEqual(result["run_state"]["status"], "completed")
            self.assertTrue(any(a["type"] == "generate_suggestion" for a in result["suggested_actions"]))
            self.assertTrue(any(ref["type"] == "issue" for ref in result["source_refs"]))

    def test_build_chat_response_uses_model_output_when_llm_is_provided(self):
        class FakeLLM:
            def invoke(self, prompt):
                self.prompt = prompt

                class Result:
                    content = (
                        '{"message":"模型回答：建议先补齐验收标准。",'
                        '"suggested_actions":[{"type":"generate_suggestion","label":"生成修改建议"}],'
                        '"source_refs":[{"type":"issue","id":"[高-1]","name":"验收标准缺失","excerpt":"缺少失败场景"}],'
                        '"target_issue_id":"[高-1]"}'
                    )

                return Result()

        session = {
            "status": "completed",
            "preset": "normal",
            "file_path": None,
            "progress": 100.0,
            "current_dimension": None,
            "completed_dimensions": [],
            "report": {
                "total_score": 76.0,
                "recommendation": "修改后通过",
                "summary": "demo",
                "issues": [
                    {
                        "id": "[高-1]",
                        "severity": "HIGH",
                        "title": "验收标准缺失",
                        "dimension": "需求完整性",
                        "description": "缺少失败场景",
                        "suggestion": "补充失败重试说明",
                    }
                ],
            },
        }

        result = build_chat_response(
            session=session,
            message="解释一下为什么",
            selected_issue_id="[高-1]",
            context_mode="default",
            llm=FakeLLM(),
        )

        self.assertEqual(result["message"], "模型回答：建议先补齐验收标准。")
        self.assertEqual(result["response_mode"], "model")
        self.assertEqual(result["assistant_status"], "model")
        self.assertEqual(result["target_issue_id"], "[高-1]")
        self.assertEqual(result["suggested_actions"][0]["type"], "generate_suggestion")

    def test_build_chat_response_gracefully_handles_docx_file_excerpt_lookup(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            prd_path = Path(tmpdir) / "demo.docx"
            prd_path.write_bytes(b"PK\x03\x04\xff\xfe\x00binary-docx-content")
            session = {
                "status": "completed",
                "preset": "normal",
                "file_path": str(prd_path),
                "progress": 100.0,
                "current_dimension": None,
                "completed_dimensions": ["需求完整性"],
                "report": {
                    "total_score": 76.0,
                    "recommendation": "修改后通过",
                    "summary": "综合评分 76.0/100，建议：修改后通过",
                    "issues": [
                        {
                            "id": "HIGH-1",
                            "severity": "HIGH",
                            "title": "验收标准缺失",
                            "dimension": "需求完整性",
                            "description": "缺少失败与异常场景",
                            "suggestion": "补充失败重试说明",
                        }
                    ],
                },
            }

            with patch("services.chat_service.resolve_minimax_config", return_value={
                "model": "MiniMax-M2.7",
                "api_key": None,
                "api_base": "https://api.minimax.chat/v1",
            }):
                result = build_chat_response(
                    session=session,
                    message="帮我解释一下当前结论",
                    selected_issue_id="HIGH-1",
                    context_mode="default",
                )

            self.assertIn("当前总分 76.0/100", result["message"])
            self.assertEqual(result["target_issue_id"], "HIGH-1")
            self.assertEqual(len(result["source_refs"]), 1)
            self.assertEqual(result["source_refs"][0]["type"], "issue")

    def test_build_chat_response_uses_dotenv_key_via_minimax_config_when_env_missing(self):
        class FakeLLM:
            def invoke(self, prompt):
                class Result:
                    content = (
                        '{"message":"模型回答：这是 HIGH 的具体问题。",'
                        '"suggested_actions":[{"type":"generate_suggestion","label":"生成修改建议"}],'
                        '"source_refs":[{"type":"issue","id":"HIGH-1","name":"缺失功能交互流程的完整描述","excerpt":"未描述主流程与异常分支的交互路径"}],'
                        '"target_issue_id":"HIGH-1"}'
                    )

                return Result()

        session = {
            "status": "completed",
            "preset": "normal",
            "file_path": None,
            "progress": 100.0,
            "current_dimension": None,
            "completed_dimensions": [],
            "report": {
                "total_score": 68.0,
                "recommendation": "修改后通过",
                "summary": "demo",
                "issues": [
                    {
                        "id": "HIGH-1",
                        "severity": "HIGH",
                        "title": "缺失功能交互流程的完整描述",
                        "dimension": "需求完整性",
                        "description": "未描述主流程与异常分支的交互路径",
                        "suggestion": "补充主流程、分支流程、异常状态和跳转关系",
                    }
                ],
            },
        }

        with patch("services.chat_service.resolve_minimax_config", return_value={
            "model": "MiniMax-M2.7",
            "api_key": "dotenv-key",
            "api_base": "https://api.minimax.chat/v1",
        }, create=True), patch("services.chat_service.get_minimax_client", return_value=FakeLLM()):
            result = build_chat_response(
                session=session,
                message="HIGH具体有什么问题",
                selected_issue_id="HIGH-1",
                context_mode="default",
            )

        self.assertIn("HIGH 的具体问题", result["message"])
        self.assertEqual(result["target_issue_id"], "HIGH-1")

    def test_build_chat_response_handles_custom_suggestion_prompt_without_model(self):
        session = {
            "status": "completed",
            "preset": "normal",
            "file_path": None,
            "progress": 100.0,
            "current_dimension": None,
            "completed_dimensions": [],
            "report": {
                "total_score": 68.0,
                "recommendation": "修改后通过",
                "summary": "demo",
                "issues": [
                    {
                        "id": "HIGH-1",
                        "severity": "HIGH",
                        "title": "缺失功能交互流程的完整描述",
                        "dimension": "需求完整性",
                        "description": "未描述主流程与异常分支的交互路径",
                        "suggestion": "补充主流程、分支流程、异常状态和跳转关系",
                    }
                ],
            },
        }

        with patch("services.chat_service.resolve_minimax_config", return_value={
            "model": "MiniMax-M2.7",
            "api_key": None,
            "api_base": "https://api.minimax.chat/v1",
        }):
            result = build_chat_response(
                session=session,
                message="请围绕问题「缺失功能交互流程的完整描述」给出修改建议",
                selected_issue_id="HIGH-1",
                context_mode="default",
            )

        self.assertIn("建议", result["message"])
        self.assertIn("补充主流程", result["message"])
        self.assertEqual(result["target_issue_id"], "HIGH-1")

    def test_build_chat_response_can_switch_issue_by_message_identifier_without_model(self):
        session = {
            "status": "completed",
            "preset": "normal",
            "file_path": None,
            "progress": 100.0,
            "current_dimension": None,
            "completed_dimensions": [],
            "report": {
                "total_score": 68.0,
                "recommendation": "修改后通过",
                "summary": "demo",
                "issues": [
                    {
                        "id": "HIGH-1",
                        "severity": "HIGH",
                        "title": "缺失功能交互流程的完整描述",
                        "dimension": "需求完整性",
                        "description": "未描述主流程与异常分支的交互路径",
                        "suggestion": "补充主流程、分支流程、异常状态和跳转关系",
                    },
                    {
                        "id": "HIGH-2",
                        "severity": "HIGH",
                        "title": "缺少关键业务规则",
                        "dimension": "需求合理性",
                        "description": "关键规则未定义",
                        "suggestion": "补充规则定义与边界",
                    },
                ],
            },
        }

        with patch("services.chat_service.resolve_minimax_config", return_value={
            "model": "MiniMax-M2.7",
            "api_key": None,
            "api_base": "https://api.minimax.chat/v1",
        }):
            result = build_chat_response(
                session=session,
                message="HIGH-2具体有什么问题",
                selected_issue_id="HIGH-1",
                context_mode="default",
            )

        self.assertEqual(result["target_issue_id"], "HIGH-2")
        self.assertIn("HIGH-2", result["message"])
        self.assertIn("关键规则未定义", result["message"])

    def test_build_chat_response_marks_model_unavailable_when_no_key(self):
        session = {
            "status": "completed",
            "preset": "normal",
            "file_path": None,
            "progress": 100.0,
            "current_dimension": None,
            "completed_dimensions": [],
            "report": {
                "total_score": 68.0,
                "recommendation": "修改后通过",
                "summary": "demo",
                "issues": [
                    {
                        "id": "HIGH-1",
                        "display_id": "HIGH-1",
                        "issue_key": "issue::abc123",
                        "severity": "HIGH",
                        "title": "缺失功能交互流程的完整描述",
                        "dimension": "需求完整性",
                        "description": "未描述主流程与异常分支的交互路径",
                        "suggestion": "补充主流程、分支流程、异常状态和跳转关系",
                    }
                ],
            },
        }

        with patch("services.chat_service.resolve_minimax_config", return_value={
            "model": "MiniMax-M2.7",
            "api_key": None,
            "api_base": "https://api.minimax.chat/v1",
        }):
            result = build_chat_response(
                session=session,
                message="请围绕问题「缺失功能交互流程的完整描述」给出修改建议",
                selected_issue_id="HIGH-1",
                context_mode="default",
            )

        self.assertEqual(result["response_mode"], "report_level")
        self.assertEqual(result["assistant_status"], "unavailable")
        self.assertEqual(result["selected_issue"]["display_id"], "HIGH-1")
        self.assertEqual(result["selected_issue"]["issue_key"], "issue::abc123")

    def test_build_chat_response_can_select_issue_by_issue_key(self):
        session = {
            "status": "completed",
            "preset": "normal",
            "file_path": None,
            "progress": 100.0,
            "current_dimension": None,
            "completed_dimensions": [],
            "report": {
                "total_score": 68.0,
                "recommendation": "修改后通过",
                "summary": "demo",
                "issues": [
                    {
                        "id": "HIGH-1",
                        "display_id": "HIGH-1",
                        "issue_key": "issue::abc123",
                        "severity": "HIGH",
                        "title": "缺失功能交互流程的完整描述",
                        "dimension": "需求完整性",
                        "description": "未描述主流程与异常分支的交互路径",
                        "suggestion": "补充主流程、分支流程、异常状态和跳转关系",
                    },
                    {
                        "id": "HIGH-2",
                        "display_id": "HIGH-2",
                        "issue_key": "issue::def456",
                        "severity": "HIGH",
                        "title": "缺少关键业务规则",
                        "dimension": "需求合理性",
                        "description": "关键规则未定义",
                        "suggestion": "补充规则定义与边界",
                    },
                ],
            },
        }

        with patch("services.chat_service.resolve_minimax_config", return_value={
            "model": "MiniMax-M2.7",
            "api_key": None,
            "api_base": "https://api.minimax.chat/v1",
        }):
            result = build_chat_response(
                session=session,
                message="请解释一下这个问题",
                selected_issue_id="issue::def456",
                context_mode="default",
            )

        self.assertEqual(result["target_issue_id"], "HIGH-2")
        self.assertEqual(result["selected_issue"]["issue_key"], "issue::def456")
        self.assertEqual(result["selected_issue"]["display_id"], "HIGH-2")

    def test_chat_response_marks_retry_action_on_model_error(self):
        class BrokenLLM:
            def invoke(self, prompt):
                raise RuntimeError("boom")

        session = {
            "status": "completed",
            "preset": "normal",
            "file_path": None,
            "progress": 100.0,
            "current_dimension": None,
            "completed_dimensions": [],
            "report": {
                "total_score": 68.0,
                "recommendation": "修改后通过",
                "summary": "demo",
                "issues": [
                    {
                        "id": "HIGH-1",
                        "display_id": "HIGH-1",
                        "issue_key": "issue::abc123",
                        "severity": "HIGH",
                        "title": "缺失功能交互流程的完整描述",
                        "dimension": "需求完整性",
                        "description": "未描述主流程与异常分支的交互路径",
                        "suggestion": "补充主流程、分支流程、异常状态和跳转关系",
                    }
                ],
            },
        }

        result = build_chat_response(
            session=session,
            message="请围绕这个问题给出修改建议",
            selected_issue_id="HIGH-1",
            context_mode="default",
            llm=BrokenLLM(),
        )

        self.assertEqual(result["assistant_status"], "error")
        self.assertEqual(result["response_mode"], "error")
        self.assertTrue(any(item["type"] == "retry_chat" for item in result["suggested_actions"]))

    def test_chat_response_asks_user_to_choose_issue_when_prompt_is_ambiguous(self):
        session = {
            "status": "completed",
            "preset": "normal",
            "file_path": None,
            "progress": 100.0,
            "current_dimension": None,
            "completed_dimensions": [],
            "report": {
                "total_score": 68.0,
                "recommendation": "修改后通过",
                "summary": "demo",
                "issues": [
                    {
                        "id": "HIGH-1",
                        "display_id": "HIGH-1",
                        "issue_key": "issue::abc123",
                        "severity": "HIGH",
                        "title": "缺失功能交互流程的完整描述",
                        "dimension": "需求完整性",
                        "description": "未描述主流程与异常分支的交互路径",
                        "suggestion": "补充主流程、分支流程、异常状态和跳转关系",
                    },
                    {
                        "id": "HIGH-2",
                        "display_id": "HIGH-2",
                        "issue_key": "issue::def456",
                        "severity": "HIGH",
                        "title": "缺少关键业务规则",
                        "dimension": "需求合理性",
                        "description": "关键规则未定义",
                        "suggestion": "补充规则定义与边界",
                    },
                ],
            },
        }

        with patch("services.chat_service.resolve_minimax_config", return_value={
            "model": "MiniMax-M2.7",
            "api_key": None,
            "api_base": "https://api.minimax.chat/v1",
        }):
            result = build_chat_response(
                session=session,
                message="HIGH 具体有什么问题",
                selected_issue_id=None,
                context_mode="default",
            )

        self.assertIn("请选择具体问题", result["message"])
        self.assertIn("HIGH-1", result["message"])
        self.assertIn("HIGH-2", result["message"])
        self.assertIsNone(result["selected_issue"])
        self.assertIsNone(result["target_issue_id"])


if __name__ == "__main__":
    unittest.main()
