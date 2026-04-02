# PRD 评审助手重构实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the assistant answer issue-specific prompts reliably, keep issue focus aligned with the current report, and show model availability explicitly instead of falling back to a generic sentence.

**Architecture:** Keep the current review pipeline and report page intact. Add a stable issue identity on the backend, teach the chat service to resolve issue context from either selected state or prompt text, and return explicit assistant status fields. On the frontend, keep the existing assistant page but split the visible state into focused issue, model status, and chat output so the user can see whether a reply is personalized or degraded.

**Tech Stack:** Python 3.11, FastAPI, Pydantic v2, Vue 3, Vite, Node test runner, unittest.

---

### Task 1: Backend issue identity and report contracts

**Files:**
- Modify: `backend/utils/report_utils.py`
- Modify: `backend/agents/reporter.py`
- Modify: `backend/services/review_service.py`
- Modify: `backend/api/schemas.py`
- Create: `tests/test_issue_identity.py`
- Test: `tests/test_reporter_score.py`
- Test: `tests/test_reviewer_errors.py`

- [ ] **Step 1: Write the failing report identity test**

```python
import unittest

from utils.report_utils import build_issue_key


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
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `python3 -m unittest -q tests.test_issue_identity`
Expected: FAIL because `build_issue_key` does not exist yet and report identity is still tied only to display numbering.

- [ ] **Step 3: Implement stable issue identity and response schema fields**

Update the report finalization path so every issue includes:

1. `display_id`
2. `issue_key`

Keep the current severity-based numbering as the display id and derive a stable `issue_key` from the issue fingerprint.

```python
# backend/utils/report_utils.py
import hashlib

def build_issue_key(issue: dict) -> str:
    fingerprint = "|".join(
        str(issue.get(field, "")).strip().lower()
        for field in ("severity", "dimension", "title", "description", "suggestion")
    )
    digest = hashlib.sha1(fingerprint.encode("utf-8")).hexdigest()[:12]
    return f"issue::{digest}"
```

```python
# backend/api/schemas.py
class ChatResponse(BaseModel):
    message: str
    response_mode: str
    assistant_status: str
    selected_issue: dict | None = None
    suggested_actions: list[SuggestedAction] = Field(default_factory=list)
    source_refs: list[SourceRef] = Field(default_factory=list)
    run_state: dict = Field(default_factory=dict)
```

```python
# backend/agents/reporter.py or backend/services/review_service.py
for issue in all_issues:
    issue["display_id"] = issue["id"]
    issue["issue_key"] = build_issue_key(issue)
```

- [ ] **Step 4: Run the tests to verify they pass**

Run:

```bash
python3 -m unittest -q tests.test_reporter_score tests.test_reviewer_errors
python3 -m unittest discover -q
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/utils/report_utils.py backend/agents/reporter.py backend/services/review_service.py backend/api/schemas.py tests/test_reporter_score.py tests/test_reviewer_errors.py
git commit -m "feat: add stable issue identity to reports"
```

### Task 2: Backend chat routing and model status

**Files:**
- Modify: `backend/services/chat_service.py`
- Modify: `backend/api/routes.py`
- Test: `tests/test_chat_service.py`
- Test: `tests/test_chat_route.py`

- [ ] **Step 1: Write the failing chat resolution tests**

```python
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
    def test_build_chat_response_prefers_prompt_issue_identifier(self):
        session = {
            "status": "completed",
            "preset": "normal",
            "file_path": None,
            "progress": 100.0,
            "current_dimension": None,
            "completed_dimensions": [],
            "report": {
                "total_score": 6.8,
                "recommendation": "MODIFY",
                "summary": "demo",
                "issues": [
                    {
                        "id": "HIGH-1",
                        "issue_key": "issue-a",
                        "severity": "HIGH",
                        "title": "缺失功能交互流程的完整描述",
                        "dimension": "需求完整性",
                        "description": "未描述主流程与异常分支的交互路径",
                        "suggestion": "补充主流程、分支流程、异常状态和跳转关系",
                    },
                    {
                        "id": "HIGH-2",
                        "issue_key": "issue-b",
                        "severity": "HIGH",
                        "title": "缺少关键业务规则",
                        "dimension": "需求合理性",
                        "description": "关键规则未定义",
                        "suggestion": "补充规则定义与边界",
                    },
                ],
            },
        }

        with patch("services.chat_service.resolve_minimax_config", return_value={"api_key": None}):
            result = build_chat_response(
                session=session,
                message="HIGH-2具体有什么问题",
                selected_issue_id="HIGH-1",
                context_mode="default",
            )

        self.assertEqual(result["target_issue_id"], "HIGH-2")
        self.assertIn("缺少关键业务规则", result["message"])
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `python3 -m unittest -q tests.test_chat_service`
Expected: FAIL because the current resolver still prefers the selected issue and the assistant still returns a generic fallback sentence for non-whitelisted prompts.

- [ ] **Step 3: Implement prompt-aware issue resolution and explicit assistant status**

Add a small deterministic resolver that chooses an issue in this order:

1. `issue_key`
2. `display_id`
3. title substring match
4. prompt keyword fallback

Then update the reply builder so it returns different response modes:

1. `model` when a structured model response is parsed successfully.
2. `report_level` when the prompt is answered from report context without a model.
3. `unavailable` when no usable model key exists.
4. `error` when the model path fails or returns malformed output.

```python
# backend/services/chat_service.py
def _has_model_key() -> bool:
    return bool(resolve_minimax_config(model=os.getenv("MINIMAX_CHAT_MODEL", "MiniMax-M2.7")).get("api_key"))

def _compact_issue(issue: dict | None) -> dict | None:
    if not issue:
        return None
    return {
        "issue_key": issue.get("issue_key"),
        "display_id": issue.get("display_id") or issue.get("id"),
        "title": issue.get("title"),
        "dimension": issue.get("dimension"),
        "severity": issue.get("severity"),
    }

def build_chat_response(session, message, selected_issue_id, context_mode="default", llm=None):
    report = session.get("report", {})
    issues = report.get("issues", [])
    issue = _resolve_issue(issues, selected_issue_id, message)
    model_response = _try_model_response(session, message, issue, _build_run_state(session, report), context_mode, llm)
    if model_response:
        return model_response

    assistant_status = "unavailable" if not _has_model_key() else "error"
    return {
        "message": _compose_message(message, report, issue, _build_run_state(session, report), context_mode),
        "response_mode": "report_level",
        "assistant_status": assistant_status,
        "selected_issue": _compact_issue(issue),
        "suggested_actions": _compose_actions(session, issue),
        "source_refs": _compose_source_refs(session, issue, message),
        "run_state": _build_run_state(session, report),
    }

def _build_run_state(session, report):
    return {
        "status": session.get("status", "unknown"),
        "progress": session.get("progress", 0.0),
        "current_dimension": session.get("current_dimension"),
        "completed_dimensions": session.get("completed_dimensions", []),
        "total_score": report.get("total_score"),
        "recommendation": report.get("recommendation"),
    }
```

Update `backend/api/routes.py` so the API still returns the same endpoint path, but now serializes the expanded chat response contract.

- [ ] **Step 4: Run the tests to verify they pass**

Run:

```bash
python3 -m unittest -q tests.test_chat_service tests.test_chat_route
python3 -m unittest discover -q
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/services/chat_service.py backend/api/routes.py tests/test_chat_service.py tests/test_chat_route.py
git commit -m "feat: make assistant responses issue-aware"
```

### Task 3: Frontend assistant state and issue focus

**Files:**
- Modify: `frontend/src/App.vue`
- Modify: `frontend/src/components/AssistantPanel.vue`
- Modify: `frontend/src/components/ReportViewer.vue`
- Modify: `frontend/src/lib/assistantPanel.js`
- Test: `frontend/tests/assistantPanel.test.mjs`
- Test: `frontend/tests/reportViewer.test.mjs`

- [ ] **Step 1: Write the failing frontend state test**

```javascript
import test from 'node:test'
import assert from 'node:assert/strict'

import { findIssueById } from '../src/lib/assistantPanel.js'

test('findIssueById resolves stable issue identity from the current report', () => {
  const report = {
    issueGroups: [
      {
        severity: 'HIGH',
        issues: [
          { id: 'HIGH-1', issue_key: 'issue-a', title: 'A' },
          { id: 'HIGH-2', issue_key: 'issue-b', title: 'B' },
        ],
      },
    ],
  }

  assert.equal(findIssueById(report, 'issue-b')?.title, 'B')
})
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `node --test frontend/tests/assistantPanel.test.mjs`
Expected: FAIL because the current helper only matches display ids and does not yet resolve `issue_key`.

- [ ] **Step 3: Split assistant UI into focused sections**

Refactor the assistant page so it visibly separates:

1. Focused issue context
2. Model status
3. Conversation thread

Use the existing `AssistantPanel` as the main container, but pass structured focused-issue data instead of only raw ids.

```vue
<!-- frontend/src/App.vue -->
<AssistantPanel
  :chat-messages="chatMessages"
  :snapshot="assistantSnapshot"
  :selected-issue="selectedIssue"
  :assistant-status="assistantStatus"
  :source-refs="assistantSourceRefs"
  @select-issue="handleIssueSelectionById"
  @send-message="submitChatMessage"
/>
```

Add a visible model badge in the panel so the user can see whether the reply is personalized, unavailable, or degraded.

- [ ] **Step 4: Run the tests to verify they pass**

Run:

```bash
node --test frontend/tests/assistantPanel.test.mjs frontend/tests/reportViewer.test.mjs
npm test
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/App.vue frontend/src/components/AssistantPanel.vue frontend/src/components/ReportViewer.vue frontend/src/lib/assistantPanel.js frontend/tests/assistantPanel.test.mjs frontend/tests/reportViewer.test.mjs
git commit -m "feat: stabilize assistant issue focus"
```

### Task 4: Frontend model-status handling and end-to-end verification

**Files:**
- Modify: `frontend/src/lib/reviewApi.js`
- Modify: `frontend/src/lib/chatApi.js`
- Modify: `frontend/src/App.vue`
- Test: `frontend/tests/chatApi.test.mjs`
- Test: `frontend/tests/reviewApi.test.mjs`

- [ ] **Step 1: Write the failing model-status test**

```javascript
import test from 'node:test'
import assert from 'node:assert/strict'

import { createReviewStream } from '../src/lib/reviewApi.js'

test('createReviewStream reports transport loss separately from backend error', () => {
  class FakeEventSource {
    static CONNECTING = 0
    static OPEN = 1
    static CLOSED = 2
    constructor(url) {
      this.url = url
      this.readyState = FakeEventSource.CONNECTING
      this.handlers = new Map()
    }
    addEventListener(name, handler) {
      this.handlers.set(name, handler)
    }
    close() {}
  }

  const errors = []
  createReviewStream({
    baseUrl: '/api',
    sessionId: 'session-1',
    EventSourceImpl: FakeEventSource,
    onError(payload) {
      errors.push(payload)
    },
  })

  assert.equal(errors.length, 1)
  assert.deepEqual(errors[0], {
    message: '评审连接中断，正在重连',
    recoverable: true,
  })
})
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `node --test frontend/tests/reviewApi.test.mjs`
Expected: FAIL because the current stream handler still treats missing SSE data as a plain failure.

- [ ] **Step 3: Implement explicit assistant status rendering**

Teach the frontend to interpret the new backend response contract:

1. `model` => render personalized answer.
2. `report_level` => render deterministic report-aware answer.
3. `unavailable` => render a clear model-unavailable banner.
4. `error` => render an error banner while preserving the report thread.

Also update `submitChatMessage()` so it keeps the current issue focus and shows the selected issue title/label in the thread header.

```javascript
// frontend/src/App.vue
const assistantStatus = ref('available')
const assistantResponseMode = ref('report_level')

// when a chat request finishes:
assistantStatus.value = normalized.assistantStatus || 'available'
assistantResponseMode.value = normalized.responseMode || 'report_level'
```

- [ ] **Step 4: Run the tests and full build**

Run:

```bash
node --test frontend/tests/reviewApi.test.mjs frontend/tests/chatApi.test.mjs
npm test
npm run build
python3 -m unittest discover -q
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/lib/reviewApi.js frontend/src/lib/chatApi.js frontend/src/App.vue frontend/tests/reviewApi.test.mjs frontend/tests/chatApi.test.mjs
git commit -m "feat: expose assistant model status"
```

## 5. Acceptance Criteria

The refactor is complete when:

1. Clicking any issue on the report page keeps the assistant focused on that same issue.
2. Typing a prompt that names a specific issue resolves to the matching issue instead of the first high-severity item.
3. Personalized replies only appear when the model is actually available.
4. Model-unavailable and model-error states are visible and explicit.
5. The current review flow, report page, and SSE progress stream still work.
