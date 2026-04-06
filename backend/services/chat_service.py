import json
import os
import re
from pathlib import Path
from typing import Any, Optional

from utils.minimax_client import get_minimax_client, resolve_minimax_config


ALLOWED_ACTION_TYPES = {
    "rerun": "重新评审",
    "switch_preset": "切换 preset",
    "focus_issue": "聚焦该问题",
    "generate_suggestion": "生成修改建议",
    "retry_chat": "重试回答",
}


def build_chat_response(
    session: dict[str, Any],
    message: str,
    selected_issue_id: Optional[str],
    context_mode: str = "default",
    llm: Any = None,
) -> dict[str, Any]:
    report = session.get("report", {})
    issues = report.get("issues", [])
    issue = _resolve_issue(issues, selected_issue_id, message)
    run_state = _build_run_state(session, report)

    model_response, assistant_status = _try_model_response(
        session=session,
        message=message,
        selected_issue=issue,
        run_state=run_state,
        context_mode=context_mode,
        llm=llm,
    )

    if model_response:
        return model_response

    response_mode = "report_level" if assistant_status == "unavailable" else "error"
    message_body = _compose_message(message, report, issue, run_state, context_mode)
    source_refs = _compose_source_refs(session, issue, message)
    suggested_actions = _compose_actions(session, issue, assistant_status)

    return {
        "message": message_body,
        "response_mode": response_mode,
        "assistant_status": assistant_status,
        "selected_issue": _compact_issue(issue),
        "suggested_actions": suggested_actions,
        "source_refs": source_refs,
        "target_issue_id": issue.get("id") if issue else selected_issue_id,
        "run_state": run_state,
    }


def _try_model_response(
    session: dict[str, Any],
    message: str,
    selected_issue: Optional[dict[str, Any]],
    run_state: dict[str, Any],
    context_mode: str,
    llm: Any = None,
) -> tuple[Optional[dict[str, Any]], str]:
    try:
        config = None
        if llm is None:
            config = resolve_minimax_config(
                model=os.getenv("MINIMAX_CHAT_MODEL")
            )
            if not config.get("api_key"):
                return None, "unavailable"

        client = llm or get_minimax_client(
            model=(config or {}).get("model", os.getenv("MINIMAX_CHAT_MODEL", "MiniMax-M2.7")),
            api_key=(config or {}).get("api_key"),
            api_base=(config or {}).get("api_base"),
            streaming=False,
            temperature=0.2,
        )
        prompt = _build_model_prompt(session, message, selected_issue, run_state, context_mode)
        raw_response = client.invoke(prompt)
        content = raw_response.content if hasattr(raw_response, "content") else str(raw_response)
        parsed = _parse_model_response(content)
        if not parsed:
            return None, "error"

        parsed["run_state"] = run_state
        parsed["target_issue_id"] = parsed.get("target_issue_id") or (
            selected_issue.get("id") if selected_issue else None
        )

        parsed["suggested_actions"] = _sanitize_actions(parsed.get("suggested_actions", []), session, selected_issue)
        parsed["source_refs"] = _sanitize_source_refs(parsed.get("source_refs", []), session, selected_issue, message)
        if not parsed["message"]:
            parsed["message"] = _compose_message(message, session.get("report", {}), selected_issue, run_state, context_mode)

        parsed["response_mode"] = "model"
        parsed["assistant_status"] = "model"
        parsed["selected_issue"] = _compact_issue(selected_issue)
        return parsed, "model"
    except Exception:
        return None, "error"


def _build_run_state(session: dict[str, Any], report: dict[str, Any]) -> dict[str, Any]:
    return {
        "status": session.get("status", "unknown"),
        "progress": session.get("progress", 0.0),
        "current_dimension": session.get("current_dimension"),
        "completed_dimensions": session.get("completed_dimensions", []),
        "total_score": report.get("total_score"),
        "recommendation": report.get("recommendation"),
    }


def _compact_issue(issue: Optional[dict[str, Any]]) -> Optional[dict[str, Any]]:
    if not issue:
        return None

    display_id = issue.get("display_id") or issue.get("id")
    return {
        "issue_key": issue.get("issue_key"),
        "display_id": display_id,
        "id": issue.get("id") or display_id,
        "title": issue.get("title"),
        "dimension": issue.get("dimension"),
        "severity": issue.get("severity"),
    }


def _build_model_prompt(
    session: dict[str, Any],
    message: str,
    selected_issue: Optional[dict[str, Any]],
    run_state: dict[str, Any],
    context_mode: str,
) -> str:
    report = session.get("report", {})
    prd_excerpt = _find_prd_excerpt(session.get("file_path"), selected_issue, message)
    context = {
        "session_id": session.get("session_id"),
        "context_mode": context_mode,
        "run_state": run_state,
        "report_summary": {
            "total_score": report.get("total_score"),
            "recommendation": report.get("recommendation"),
            "summary": report.get("summary"),
        },
        "selected_issue": selected_issue,
        "prd_excerpt": prd_excerpt,
        "allowed_actions": list(ALLOWED_ACTION_TYPES.keys()),
    }

    return (
        "你是 PRD 评审工作台中的引导式对话助手。"
        "请用中文回答，语气清晰、直接、不过度展开。"
        "你只能输出严格 JSON，不要输出 markdown、代码块或额外解释。"
        "JSON 必须包含 message、suggested_actions、source_refs、target_issue_id 四个字段。"
        "suggested_actions 中的 type 只能是 rerun、switch_preset、focus_issue、generate_suggestion、retry_chat。"
        "source_refs 中尽量引用当前问题或 PRD 原文片段。"
        "如果信息不足，请明确说明并给出下一步建议。\n\n"
        f"用户问题：{message}\n\n"
        f"上下文：{json.dumps(context, ensure_ascii=False, indent=2)}"
    )


def _parse_model_response(content: str) -> Optional[dict[str, Any]]:
    if not content:
        return None

    text = content.strip()
    if "```" in text:
        parts = text.split("```")
        for part in parts:
            candidate = part.strip()
            if candidate.startswith("{") and candidate.endswith("}"):
                text = candidate
                break

    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return None

    try:
        parsed = json.loads(text[start : end + 1])
    except json.JSONDecodeError:
        return None

    return {
        "message": str(parsed.get("message", "")).strip(),
        "suggested_actions": parsed.get("suggested_actions", []),
        "source_refs": parsed.get("source_refs", []),
        "target_issue_id": parsed.get("target_issue_id"),
    }


def _sanitize_actions(
    actions: list[dict[str, Any]],
    session: dict[str, Any],
    issue: Optional[dict[str, Any]],
) -> list[dict[str, Any]]:
    cleaned: list[dict[str, Any]] = []
    preset = session.get("preset", "normal")

    for action in actions:
        action_type = action.get("type")
        if action_type not in ALLOWED_ACTION_TYPES:
            continue

        item = {
            "type": action_type,
            "label": action.get("label") or ALLOWED_ACTION_TYPES[action_type],
        }

        if action_type == "switch_preset":
            item["preset"] = action.get("preset") or preset
        if action_type == "focus_issue":
            item["issue_id"] = action.get("issue_id") or (issue.get("id") if issue else None)

        cleaned.append(item)

    if not cleaned:
        cleaned = _compose_actions(session, issue)

    return cleaned


def _sanitize_source_refs(
    source_refs: list[dict[str, Any]],
    session: dict[str, Any],
    issue: Optional[dict[str, Any]],
    message: str,
) -> list[dict[str, Any]]:
    cleaned: list[dict[str, Any]] = []
    for ref in source_refs:
        ref_type = ref.get("type")
        if ref_type not in {"issue", "section"}:
            continue

        item = {
            "type": ref_type,
            "id": ref.get("id"),
            "name": ref.get("name"),
            "excerpt": ref.get("excerpt"),
        }
        cleaned.append(item)

    if not cleaned:
        cleaned = _compose_source_refs(session, issue, message)

    return cleaned


def _find_issue(
    issues: list[dict[str, Any]],
    selected_issue_id: Optional[str],
) -> Optional[dict[str, Any]]:
    if not selected_issue_id:
        return None

    target = _normalize_issue_identifier(selected_issue_id)
    for issue in issues:
        for field in ("issue_key", "display_id", "id"):
            if _normalize_issue_identifier(issue.get(field)) == target:
                return issue

        if issue.get("id") == selected_issue_id:
            return issue

    return None


def _resolve_issue(
    issues: list[dict[str, Any]],
    selected_issue_id: Optional[str],
    message: str,
) -> Optional[dict[str, Any]]:
    selected = _find_issue(issues, selected_issue_id)
    by_message = _find_issue_from_message(issues, message)

    if by_message:
        return by_message
    if selected:
        return selected
    if len(issues) == 1 and _is_issue_specific_prompt(message):
        return issues[0]
    return None


def _find_issue_from_message(
    issues: list[dict[str, Any]],
    message: str,
) -> Optional[dict[str, Any]]:
    if not issues or not message:
        return None

    compact = _normalize_issue_identifier(message)

    issue_key = re.search(r"issue::[a-f0-9]{12}", compact)
    if issue_key:
        candidate = _normalize_issue_identifier(issue_key.group(0))
        for issue in issues:
            if _normalize_issue_identifier(issue.get("issue_key")) == candidate:
                return issue

    direct_id = re.search(r"(HIGH|MEDIUM|LOW)[-_]?(\d+)", compact)
    if direct_id:
        candidate = f"{direct_id.group(1)}-{direct_id.group(2)}"
        for issue in issues:
            if _normalize_issue_identifier(issue.get("id")) == candidate:
                return issue

    cn_id = re.search(r"([高中低])[-_]?(\d+)", compact)
    if cn_id:
        severity_map = {"高": "HIGH", "中": "MEDIUM", "低": "LOW"}
        candidate = f"{severity_map[cn_id.group(1)]}-{cn_id.group(2)}"
        for issue in issues:
            if _normalize_issue_identifier(issue.get("id")) == candidate:
                return issue

    for issue in issues:
        title = str(issue.get("title", "")).strip()
        if title and title in message:
            return issue

    compact_tokens = [token for token in re.split(r"[^\w\u4e00-\u9fff]+", compact) if len(token) >= 2]
    if compact_tokens:
        scored_issue = None
        scored_value = 0
        for issue in issues:
            haystack = " ".join(
                str(issue.get(field, "")).lower()
                for field in ("title", "dimension", "description", "suggestion")
            )
            score = sum(1 for token in compact_tokens if token.lower() in haystack)
            if score > scored_value:
                scored_value = score
                scored_issue = issue
        if scored_value > 0:
            return scored_issue

    return None


def _normalize_issue_identifier(value: Any) -> str:
    text = str(value or "").strip()
    if not text:
        return ""

    compact = re.sub(r"\s+", "", text)
    compact = compact.replace("【", "[").replace("】", "]")
    compact = compact.strip("[]")
    return compact.upper()


def _compose_message(
    message: str,
    report: dict[str, Any],
    issue: Optional[dict[str, Any]],
    run_state: dict[str, Any],
    context_mode: str,
) -> str:
    total_score = report.get("total_score", "--")
    recommendation = report.get("recommendation", "PENDING")
    severity_labels = {
        "HIGH": "高优先级",
        "MEDIUM": "中优先级",
        "LOW": "低优先级",
    }
    lower_message = message.lower()

    if any(keyword in message for keyword in ["建议", "怎么改", "如何改", "优化", "修复", "改进"]):
        if issue:
            title = issue.get("title", "未命名问题")
            description = issue.get("description", "未提供描述")
            suggestion = issue.get("suggestion", "未提供修改建议")
            return (
                f"针对问题「{title}」，当前主要缺陷是：{description}。"
                f" 建议优先这样修改：{suggestion}。"
            )
        return _build_issue_choice_message(report.get("issues", []), "我还不能确定你要追问哪个问题")

    if any(keyword in message for keyword in ["什么问题", "具体问题", "问题点", "哪里有问题"]) or (
        "high" in lower_message or "medium" in lower_message or "low" in lower_message
    ):
        if issue:
            severity = issue.get("severity", "LOW")
            title = issue.get("title", "未命名问题")
            description = issue.get("description", "未提供描述")
            dimension = issue.get("dimension", "未标注维度")
            issue_id = issue.get("id", "未知编号")
            return (
                f"{issue_id}（{severity_labels.get(severity, severity)}）的问题是「{title}」，"
                f"位于{dimension}维度，具体表现为：{description}。"
            )
        return _build_issue_choice_message(report.get("issues", []), "请选择具体问题后我再展开说明")

    if "为什么" in message or "原因" in message or "解释" in message:
        if issue:
            severity = issue.get("severity", "LOW")
            title = issue.get("title", "未命名问题")
            description = issue.get("description", "未提供描述")
            return (
                f"我先看了问题「{title}」。当前总分 {total_score}/100，建议 {recommendation}。"
                f" 这个问题被标记为 {severity_labels.get(severity, severity)}，因为 {description}。"
            )
        return f"当前总分 {total_score}/100，建议 {recommendation}。我可以继续帮你解释具体问题。"

    if "哪里" in message or "原文" in message or "出处" in message:
        if issue:
            return "我已经定位到相关原文和问题上下文了，你可以看右侧来源片段。"
        return "我可以帮你定位到报告对应的原文片段。"

    if run_state.get("status") == "reviewing":
        return f"当前评审还在进行中，已完成 {len(run_state.get('completed_dimensions', []))} 个维度。"

    if context_mode == "compact":
        return f"总分 {total_score}/100，建议 {recommendation}。"

    return "我可以帮你解释当前结论、定位问题原文，或者给出修改建议。"


def _compose_actions(
    session: dict[str, Any],
    issue: Optional[dict[str, Any]],
    assistant_status: str = "unavailable",
) -> list[dict[str, Any]]:
    actions: list[dict[str, Any]] = [{"type": "generate_suggestion", "label": "生成修改建议"}]

    if assistant_status == "error":
        actions.insert(0, {"type": "retry_chat", "label": "重试回答"})

    if session.get("status") == "completed":
        actions.insert(0, {"type": "rerun", "label": "重新评审"})

    preset = session.get("preset", "normal")
    actions.append({"type": "switch_preset", "label": "切换 preset", "preset": preset})

    if issue:
        actions.append({"type": "focus_issue", "label": "聚焦该问题", "issue_id": issue.get("id")})

    return actions


def _is_issue_specific_prompt(message: str) -> bool:
    if not message:
        return False

    lower_message = message.lower()
    keywords = ["问题", "建议", "怎么改", "如何改", "优化", "修复", "解释", "原因", "high", "medium", "low", "issue::"]
    return any(keyword in lower_message for keyword in keywords)


def _build_issue_choice_message(issues: list[dict[str, Any]], prefix: str) -> str:
    if not issues:
        return "当前还没有可用的问题列表。你可以先完成一次评审，或告诉我要看的问题编号。"

    options = "；".join(
        f"{issue.get('display_id') or issue.get('id')} · {issue.get('title', '未命名问题')}"
        for issue in issues[:4]
    )
    return f"{prefix}。请选择具体问题，例如：{options}。"


def _compose_source_refs(
    session: dict[str, Any],
    issue: Optional[dict[str, Any]],
    message: str,
) -> list[dict[str, Any]]:
    refs: list[dict[str, Any]] = []
    if issue:
        refs.append(
            {
                "type": "issue",
                "id": issue.get("id"),
                "name": issue.get("title"),
                "excerpt": issue.get("description", ""),
            }
        )

    excerpt = _find_prd_excerpt(session.get("file_path"), issue, message)
    if excerpt:
        refs.append(
            {
                "type": "section",
                "name": "PRD 原文",
                "excerpt": excerpt,
            }
        )

    return refs


def _find_prd_excerpt(
    file_path: Optional[str],
    issue: Optional[dict[str, Any]],
    message: str,
) -> str:
    if not file_path:
        return ""

    path = Path(file_path)
    if not path.exists():
        return ""

    try:
        content = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return ""
    lines = content.splitlines()
    keywords: list[str] = []

    if issue:
        keywords.extend(
            [
                issue.get("title", ""),
                issue.get("dimension", ""),
                issue.get("description", ""),
            ]
        )

    keywords.extend([word for word in ["验收标准", "异常", "失败", "重试", "原文"] if word in message])
    keywords = [keyword for keyword in keywords if keyword]

    for index, line in enumerate(lines):
        if any(keyword in line for keyword in keywords):
            start = max(index - 1, 0)
            end = min(index + 2, len(lines))
            return "\n".join(lines[start:end]).strip()

    for index, line in enumerate(lines):
        if line.strip():
            start = max(index - 1, 0)
            end = min(index + 2, len(lines))
            return "\n".join(lines[start:end]).strip()

    return ""
