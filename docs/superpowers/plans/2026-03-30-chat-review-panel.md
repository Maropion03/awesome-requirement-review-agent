# PRD Review Chat Panel Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a right-side guided chat panel to the PRD review workstation so users can ask follow-up questions, inspect source context, and trigger a small set of guided actions without leaving the page.

**Architecture:** Keep the current upload → review → report flow intact. Add a lightweight backend chat endpoint that reads from the existing in-memory session state and PRD file, then returns a stable UI-friendly response with source references and suggested actions. On the frontend, split the page into a main workstation area and a persistent assistant panel that renders the conversation, context snapshot, and quick actions.

**Tech Stack:** Python 3.11, FastAPI, Pydantic v2, SSE for the existing review stream, Vue 3, Vite, Node test runner, unittest.

---

### Task 1: Backend chat service and schemas

**Files:**
- Modify: `backend/api/schemas.py`
- Create: `backend/services/chat_service.py`
- Test: `tests/test_chat_service.py`

- [ ] **Step 1: Write the failing service test**

```python
import sys
import tempfile
import unittest
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1] / "backend"
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from services.chat_service import build_chat_response


class TestChatService(unittest.TestCase):
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
                    "total_score": 7.6,
                    "recommendation": "MODIFY",
                    "summary": "综合评分 7.6/10，建议修改后通过",
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
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `python3 -m unittest -q tests.test_chat_service`
Expected: FAIL with `ModuleNotFoundError` because `services.chat_service` does not exist yet.

- [ ] **Step 3: Implement the minimal chat service and schema models**

```python
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    session_id: str
    message: str
    selected_issue_id: str | None = None
    context_mode: str = "default"


class SuggestedAction(BaseModel):
    type: str
    label: str
    issue_id: str | None = None
    preset: str | None = None


class SourceRef(BaseModel):
    type: str
    id: str | None = None
    name: str | None = None
    excerpt: str | None = None


class ChatResponse(BaseModel):
    message: str
    suggested_actions: list[SuggestedAction] = Field(default_factory=list)
    source_refs: list[SourceRef] = Field(default_factory=list)
    target_issue_id: str | None = None
    run_state: dict = Field(default_factory=dict)
```

```python
from pathlib import Path

def build_chat_response(session: dict, message: str, selected_issue_id: str | None, context_mode: str) -> dict:
    report = session.get("report", {})
    issues = report.get("issues", [])
    issue = next((item for item in issues if item.get("id") == selected_issue_id), None)
    selected_label = issue.get("title") if issue else "当前报告"

    source_refs = []
    if issue:
        source_refs.append({
            "type": "issue",
            "id": issue.get("id"),
            "name": issue.get("title"),
            "excerpt": issue.get("description", ""),
        })

    prd_excerpt = _find_prd_excerpt(session.get("file_path"), issue, message)
    if prd_excerpt:
        source_refs.append({
            "type": "section",
            "name": "PRD 原文",
            "excerpt": prd_excerpt,
        })

    if "为什么" in message or "原因" in message or "解释" in message:
        body = f"我先看了{selected_label}。当前结论是{report.get('recommendation', 'PENDING')}，总分 {report.get('total_score', '--')}/10。"
        if issue:
            body += f" 这个问题被标记为 {issue.get('severity', 'LOW')}，因为 {issue.get('description', '未提供描述')}。"
    elif "哪里" in message or "原文" in message or "出处" in message:
        body = "我已经把相关原文定位出来了，你可以直接看右侧的来源片段。"
    else:
        body = "我可以帮你解释当前结论、定位问题原文，或者给出修改建议。"

    suggested_actions = [{"type": "generate_suggestion", "label": "生成修改建议"}]
    if session.get("status") == "completed":
        suggested_actions.insert(0, {"type": "rerun", "label": "重新评审"})
    if session.get("preset"):
        suggested_actions.append({"type": "switch_preset", "label": "切换 preset", "preset": session.get("preset")})
    if issue:
        suggested_actions.append({"type": "focus_issue", "label": "聚焦该问题", "issue_id": issue.get("id")})

    return {
        "message": body,
        "suggested_actions": suggested_actions,
        "source_refs": source_refs,
        "target_issue_id": issue.get("id") if issue else selected_issue_id,
        "run_state": {
            "status": session.get("status", "unknown"),
            "progress": session.get("progress", 0.0),
            "current_dimension": session.get("current_dimension"),
            "completed_dimensions": session.get("completed_dimensions", []),
            "total_score": report.get("total_score"),
            "recommendation": report.get("recommendation"),
        },
    }


def _find_prd_excerpt(file_path: str | None, issue: dict | None, message: str) -> str:
    if not file_path:
        return ""

    path = Path(file_path)
    if not path.exists():
        return ""

    content = path.read_text(encoding="utf-8")
    lines = content.splitlines()
    keywords = []
    if issue:
        keywords.extend([issue.get("title", ""), issue.get("dimension", ""), issue.get("description", "")])
    keywords.extend([word for word in ["验收标准", "异常", "失败", "重试", "原文"] if word in message])

    for index, line in enumerate(lines):
        if any(keyword and keyword in line for keyword in keywords):
            start = max(index - 1, 0)
            end = min(index + 2, len(lines))
            return "\n".join(lines[start:end]).strip()

    for index, line in enumerate(lines):
        if line.strip():
            start = max(index - 1, 0)
            end = min(index + 2, len(lines))
            return "\n".join(lines[start:end]).strip()

    return ""
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `python3 -m unittest -q tests.test_chat_service`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/api/schemas.py backend/services/chat_service.py tests/test_chat_service.py
git commit -m "feat: add guided chat response service"
```

### Task 2: Backend `/api/review/chat` route

**Files:**
- Modify: `backend/api/routes.py`
- Test: `tests/test_chat_route.py`

- [ ] **Step 1: Write the failing route test**

```python
import sys
import unittest

from fastapi.testclient import TestClient

from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1] / "backend"
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from api import routes
from main import app


class TestChatRoute(unittest.TestCase):
    def setUp(self):
        routes.sessions.clear()
        routes.sessions["session-1"] = {
            "filename": "demo.md",
            "file_type": "markdown",
            "size": 10,
            "file_path": "uploads/demo.md",
            "status": "completed",
            "preset": "normal",
            "sse_service": None,
            "current_dimension": None,
            "completed_dimensions": [],
            "progress": 100.0,
            "dimension_scores": [],
            "report": {
                "total_score": 7.6,
                "recommendation": "MODIFY",
                "summary": "demo",
                "issues": [],
            },
        }
        self.client = TestClient(app)

    def tearDown(self):
        routes.sessions.clear()

    def test_chat_endpoint_returns_structured_response(self):
        response = self.client.post(
            "/api/review/chat",
            json={
                "session_id": "session-1",
                "message": "帮我解释一下当前结论",
                "selected_issue_id": None,
                "context_mode": "default",
            },
        )

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertIn("message", body)
        self.assertIn("suggested_actions", body)
        self.assertIn("run_state", body)
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `python3 -m unittest -q tests.test_chat_route`
Expected: FAIL with 404 or missing route.

- [ ] **Step 3: Wire the chat route to the new service**

```python
from api.schemas import ChatRequest, ChatResponse
from services.chat_service import build_chat_response


@router.post("/review/chat", response_model=ChatResponse)
async def chat_review(request: ChatRequest):
    if request.session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    session = sessions[request.session_id]
    return ChatResponse(**build_chat_response(
        session=session,
        message=request.message,
        selected_issue_id=request.selected_issue_id,
        context_mode=request.context_mode,
    ))
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `python3 -m unittest -q tests.test_chat_route`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/api/routes.py tests/test_chat_route.py
git commit -m "feat: expose guided chat endpoint"
```

### Task 3: Frontend chat API and assistant view model

**Files:**
- Create: `frontend/src/lib/chatApi.js`
- Create: `frontend/src/lib/assistantPanel.js`
- Test: `frontend/tests/chatApi.test.mjs`
- Test: `frontend/tests/assistantPanel.test.mjs`

- [ ] **Step 1: Write the failing API and view-model tests**

```javascript
import test from 'node:test'
import assert from 'node:assert/strict'

import { sendChatMessage } from '../src/lib/chatApi.js'

test('sendChatMessage posts a chat payload and returns parsed response', async () => {
  const calls = []
  const fetchImpl = async (url, options) => {
    calls.push({ url, options })
    return {
      ok: true,
      json: async () => ({
        message: '好的，我来解释',
        suggested_actions: [],
        source_refs: [],
        target_issue_id: null,
        run_state: {},
      }),
    }
  }

  const result = await sendChatMessage({
    baseUrl: 'http://127.0.0.1:8001/api',
    sessionId: 'session-1',
    message: '解释一下当前结论',
    selectedIssueId: '[高-1]',
    contextMode: 'default',
    fetchImpl,
  })

  assert.equal(result.message, '好的，我来解释')
  assert.equal(calls[0].url, 'http://127.0.0.1:8001/api/review/chat')
  assert.deepEqual(JSON.parse(calls[0].options.body), {
    session_id: 'session-1',
    message: '解释一下当前结论',
    selected_issue_id: '[高-1]',
    context_mode: 'default',
  })
})
```

```javascript
import test from 'node:test'
import assert from 'node:assert/strict'

import { buildAssistantSnapshot, normalizeChatResponse } from '../src/lib/assistantPanel.js'

test('buildAssistantSnapshot reflects report, run state, and issue context', () => {
  const snapshot = buildAssistantSnapshot({
    report: {
      score: '7.6',
      suggestion: '修改后通过',
      summary: '综合评分 7.6/10',
    },
    runState: {
      status: 'completed',
      progress: 100,
    },
    selectedIssue: {
      id: '[高-1]',
      title: '验收标准缺失',
      description: '缺少失败场景',
    },
  })

  assert.equal(snapshot.score, '7.6')
  assert.equal(snapshot.status, 'completed')
  assert.equal(snapshot.selectedIssue.id, '[高-1]')
})
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `cd frontend && node --test tests/chatApi.test.mjs tests/assistantPanel.test.mjs`
Expected: FAIL with missing modules.

- [ ] **Step 3: Implement the frontend helpers**

```javascript
const DEFAULT_API_BASE_URL =
  (typeof import.meta !== 'undefined' && import.meta.env?.VITE_API_BASE_URL) || '/api'

export async function sendChatMessage({
  baseUrl = DEFAULT_API_BASE_URL,
  sessionId,
  message,
  selectedIssueId = null,
  contextMode = 'default',
  fetchImpl = fetch,
}) {
  const response = await fetchImpl(`${String(baseUrl).replace(/\/+$/, '')}/review/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      session_id: sessionId,
      message,
      selected_issue_id: selectedIssueId,
      context_mode: contextMode,
    }),
  })

  const data = await response.json().catch(() => null)
  if (!response.ok) {
    throw new Error(data?.detail || `Request failed with status ${response.status}`)
  }
  return data
}
```

```javascript
export function buildAssistantSnapshot({ report, runState, selectedIssue }) {
  return {
    score: report?.score ?? '--',
    suggestion: report?.suggestion ?? '尚未生成',
    summary: report?.summary ?? '评审完成后将在这里显示结论。',
    status: runState?.status ?? 'idle',
    progress: runState?.progress ?? 0,
    selectedIssue: selectedIssue ?? null,
  }
}

export function normalizeChatResponse(response = {}) {
  return {
    message: response.message || '',
    suggestedActions: Array.isArray(response.suggested_actions) ? response.suggested_actions : [],
    sourceRefs: Array.isArray(response.source_refs) ? response.source_refs : [],
    targetIssueId: response.target_issue_id || null,
    runState: response.run_state || {},
  }
}

export function createAssistantState() {
  return {
    chatMessages: [],
    selectedIssue: null,
    suggestedActions: [],
  }
}
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `cd frontend && node --test tests/chatApi.test.mjs tests/assistantPanel.test.mjs`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/lib/chatApi.js frontend/src/lib/assistantPanel.js frontend/tests/chatApi.test.mjs frontend/tests/assistantPanel.test.mjs
git commit -m "feat: add frontend chat helpers"
```

### Task 4: Assistant panel UI and workstation layout

**Files:**
- Create: `frontend/src/components/AssistantPanel.vue`
- Modify: `frontend/src/App.vue`
- Modify: `frontend/src/components/ReportViewer.vue`

- [ ] **Step 1: Write the failing layout and issue-link tests**

```javascript
import test from 'node:test'
import assert from 'node:assert/strict'

import { createAssistantState } from '../src/lib/assistantPanel.js'

test('createAssistantState initializes chat history and selected issue', () => {
  const state = createAssistantState()
  assert.deepEqual(state.chatMessages, [])
  assert.equal(state.selectedIssue, null)
})
```

```javascript
import test from 'node:test'
import assert from 'node:assert/strict'

import { mapReportToViewModel } from '../src/lib/reviewApi.js'

test('mapReportToViewModel keeps issue ids available for linking', () => {
  const viewModel = mapReportToViewModel({
    total_score: 8.1,
    recommendation: 'APPROVE',
    summary: 'demo',
    dimension_scores: [],
    issues: [
      { id: '[高-1]', severity: 'HIGH', title: '问题', dimension: '需求完整性', description: 'desc' },
    ],
  })

  assert.equal(viewModel.issues[0].id, '[高-1]')
})
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `cd frontend && node --test tests/assistantPanel.test.mjs tests/reviewApi.test.mjs`
Expected: FAIL until the new state helper and click wiring exist.

- [ ] **Step 3: Implement the assistant panel and issue selection wiring**

```vue
<AssistantPanel
  :chat-messages="chatMessages"
  :snapshot="assistantSnapshot"
  :suggested-actions="suggestedActions"
  :selected-issue="selectedIssue"
  :is-running="isRunning"
  :is-loading="isChatLoading"
  @send-message="sendChatMessage"
  @run-action="handleAssistantAction"
  @select-issue="selectIssue"
/>
```

```vue
<li
  v-for="issue in group.issues"
  :key="issue.id"
  class="issue-card"
  role="button"
  tabindex="0"
  @click="$emit('issue-select', issue)"
  @keydown.enter="$emit('issue-select', issue)"
>
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `cd frontend && node --test tests/assistantPanel.test.mjs tests/reviewApi.test.mjs`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/components/AssistantPanel.vue frontend/src/App.vue frontend/src/components/ReportViewer.vue
git commit -m "feat: add guided assistant panel to review workstation"
```

### Task 5: End-to-end verification

**Files:**
- Modify: none

- [ ] **Step 1: Run the backend test suite**

Run: `python3 -m unittest discover -q`
Expected: PASS.

- [ ] **Step 2: Run the frontend test suite**

Run: `cd frontend && node --test tests/*.test.mjs`
Expected: PASS.

- [ ] **Step 3: Run the frontend production build**

Run: `cd frontend && npm run build`
Expected: PASS and produce `frontend/dist/index.html`.

- [ ] **Step 4: Smoke check the backend chat route**

Run the app:

```bash
cd backend
uvicorn main:app --reload
```

Check:

```bash
curl -X POST http://127.0.0.1:8000/api/review/chat \
  -H 'Content-Type: application/json' \
  -d '{"session_id":"demo","message":"解释一下当前结论","context_mode":"default"}'
```

Expected: JSON response with `message`, `suggested_actions`, `source_refs`, `target_issue_id`, and `run_state`.

- [ ] **Step 5: Commit verification notes**

```bash
git add .
git commit -m "test: verify conversational review panel"
```

---

## Execution Notes

1. Keep the first version intentionally narrow: explanation, issue focus, rerun, and preset switch are enough.
2. Do not replace the existing review workflow; the assistant should sit beside it.
3. Prefer deterministic helper logic first so the first version ships quickly and stays testable.
4. If the assistant panel starts to crowd the main report on smaller screens, collapse it into a stacked layout before adding more features.
