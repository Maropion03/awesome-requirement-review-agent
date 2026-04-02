# Single-Run PRD Reviewer Gap Closure Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Close the remaining product gaps for a single-run PRD review tool without adding history/workspace/team-management capabilities.

**Architecture:** Keep the current upload -> review -> report -> assistant flow. Extend the report contract so each issue carries stronger evidence and local mutable state for the current browser session. Add lightweight backend endpoints only where single-run behavior requires deterministic server output, and keep issue state / export assembly in the frontend unless persistence is necessary.

**Tech Stack:** Python 3.9+, FastAPI, unittest, Vue 3, Vite, Node test runner.

---

## Scope

**In scope**
- Evidence chain with stronger source references
- Local issue status flow inside a single report
- Exportable modification suggestions
- More reliable issue-focused assistant follow-up
- Recoverable retry for the current review run
- Direct text paste as an alternative to file upload
- Optional modified-text recheck within the same run

**Out of scope**
- History list
- Multi-session workspace
- Sharing / permissions
- External integrations
- Team assignment workflows

---

## File Structure

**Backend existing files**
- `backend/api/routes.py`
  Responsibility: expose upload/start/chat/report endpoints and add single-run helper endpoints if needed.
- `backend/api/schemas.py`
  Responsibility: request / response contracts for source refs, issue state payloads, and retry helpers.
- `backend/services/review_service.py`
  Responsibility: accept file or direct text review input and return a complete report payload.
- `backend/services/chat_service.py`
  Responsibility: assistant issue resolution, evidence-aware answering, and retry-safe reply contract.
- `backend/utils/report_utils.py`
  Responsibility: issue identity, evidence normalization, and per-issue export helpers.
- `backend/tools/parser/*`
  Responsibility: parse markdown/docx or pass through plain text if direct input is added.

**Frontend existing files**
- `frontend/src/App.vue`
  Responsibility: page orchestration, single-run state, retry actions, route changes.
- `frontend/src/components/UploadArea.vue`
  Responsibility: switch between file upload and direct text input.
- `frontend/src/components/ReportViewer.vue`
  Responsibility: render issues, evidence, local status controls, export triggers.
- `frontend/src/components/AssistantPanel.vue`
  Responsibility: issue-focused chat, retry entry, and evidence/source visibility.
- `frontend/src/lib/reviewApi.js`
  Responsibility: review/report mapping and API helpers.
- `frontend/src/lib/chatApi.js`
  Responsibility: assistant request helpers.
- `frontend/src/lib/assistantPanel.js`
  Responsibility: normalize assistant payloads and local issue lookup.

**Frontend likely new files**
- `frontend/src/lib/issueState.js`
  Responsibility: normalize local issue status and derive export payloads.
- `frontend/src/lib/exportSuggestions.js`
  Responsibility: format markdown/text export for accepted suggestions.

**Tests**
- `tests/test_issue_identity.py`
- `tests/test_chat_service.py`
- `tests/test_chat_route.py`
- `tests/test_review_service.py` or extend existing backend tests
- `frontend/tests/reviewApi.test.mjs`
- `frontend/tests/assistantPanel.test.mjs`
- `frontend/tests/uiCopy.test.mjs`
- `frontend/tests/issueState.test.mjs`

---

### Task 1: Evidence Chain Contract

**Files:**
- Modify: `backend/utils/report_utils.py`
- Modify: `backend/agents/reporter.py`
- Modify: `backend/services/review_service.py`
- Modify: `backend/api/schemas.py`
- Test: `tests/test_issue_identity.py`
- Test: `tests/test_reporter_score.py`

- [ ] **Step 1: Write the failing backend test for issue evidence fields**

```python
def test_report_issue_contains_source_excerpt_fields(self):
    report = reporter.generate_report(
        {
            "completeness": {
                "score": 7.0,
                "reasoning": "ok",
                "dimension": "需求完整性",
                "issues": [
                    {
                        "severity": "HIGH",
                        "title": "验收标准缺失",
                        "description": "未说明失败场景",
                        "suggestion": "补充失败重试与异常状态",
                        "source_quote": "验收标准：用户提交后显示成功",
                        "source_section": "验收标准",
                    }
                ],
            }
        }
    )
    issue = report["issues"][0]
    self.assertEqual(issue["source_quote"], "验收标准：用户提交后显示成功")
    self.assertEqual(issue["source_section"], "验收标准")
```

- [ ] **Step 2: Run the target test to verify it fails**

Run: `python3 -m unittest -q tests.test_reporter_score`
Expected: FAIL because source evidence fields are not guaranteed in normalized report issues.

- [ ] **Step 3: Implement minimal evidence normalization**

```python
def normalize_issue_evidence(issue):
    normalized = dict(issue)
    normalized["source_quote"] = str(issue.get("source_quote", "")).strip()
    normalized["source_section"] = str(issue.get("source_section", "")).strip()
    normalized["source_locator"] = str(issue.get("source_locator", "")).strip()
    return normalized
```

Apply this when finalizing issue payloads so every issue exposes:
- `issue_key`
- `display_id`
- `source_quote`
- `source_section`
- `source_locator`

- [ ] **Step 4: Update API schemas so frontend can rely on these fields**

```python
class ReviewIssue(BaseModel):
    id: str
    display_id: str
    issue_key: str
    severity: str
    title: str
    dimension: str
    description: str
    suggestion: str
    source_quote: str = ""
    source_section: str = ""
    source_locator: str = ""
```

- [ ] **Step 5: Re-run backend tests**

Run: `python3 -m unittest -q tests.test_issue_identity tests.test_reporter_score`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add backend/utils/report_utils.py backend/agents/reporter.py backend/services/review_service.py backend/api/schemas.py tests/test_issue_identity.py tests/test_reporter_score.py
git commit -m "feat: add evidence fields to report issues"
```

### Task 2: Frontend Evidence Rendering and Source Jump

**Files:**
- Modify: `frontend/src/lib/reviewApi.js`
- Modify: `frontend/src/components/ReportViewer.vue`
- Modify: `frontend/src/components/AssistantPanel.vue`
- Test: `frontend/tests/reviewApi.test.mjs`
- Test: `frontend/tests/uiCopy.test.mjs`

- [ ] **Step 1: Write the failing frontend mapping test**

```javascript
test('mapReportToViewModel preserves source evidence fields', () => {
  const viewModel = mapReportToViewModel({
    issues: [{
      id: 'HIGH-1',
      display_id: 'HIGH-1',
      issue_key: 'issue::abc123',
      severity: 'HIGH',
      title: '验收标准缺失',
      dimension: '需求完整性',
      description: '未说明失败场景',
      suggestion: '补充失败重试与异常状态',
      source_quote: '验收标准：用户提交后显示成功',
      source_section: '验收标准',
      source_locator: 'line:18',
    }],
  })
  assert.equal(viewModel.issues[0].sourceQuote, '验收标准：用户提交后显示成功')
})
```

- [ ] **Step 2: Run the target test to verify it fails**

Run: `node --test tests/reviewApi.test.mjs`
Expected: FAIL because `sourceQuote/sourceSection/sourceLocator` are not exposed in the view model.

- [ ] **Step 3: Implement minimal mapping and rendering**

```javascript
function normalizeIssue(issue = {}, index = 0) {
  return {
    // existing fields...
    sourceQuote: issue.source_quote || '',
    sourceSection: issue.source_section || '',
    sourceLocator: issue.source_locator || '',
  }
}
```

Render under each issue:
- quoted source snippet
- section label
- locator text

- [ ] **Step 4: Add a lightweight jump/focus interaction**

Use a simple local action in `AssistantPanel.vue` / `ReportViewer.vue`:
- clicking evidence chip focuses the issue card
- if only a quote exists, scroll to the issue block instead of pretending to jump into raw document lines

- [ ] **Step 5: Re-run frontend tests**

Run: `npm test`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add frontend/src/lib/reviewApi.js frontend/src/components/ReportViewer.vue frontend/src/components/AssistantPanel.vue frontend/tests/reviewApi.test.mjs frontend/tests/uiCopy.test.mjs
git commit -m "feat: surface evidence chain in single-run report"
```

### Task 3: Local Issue Status Flow

**Files:**
- Create: `frontend/src/lib/issueState.js`
- Modify: `frontend/src/App.vue`
- Modify: `frontend/src/components/ReportViewer.vue`
- Test: `frontend/tests/issueState.test.mjs`
- Test: `frontend/tests/uiCopy.test.mjs`

- [ ] **Step 1: Write the failing reducer-style test**

```javascript
test('issueState toggles issue review status locally', () => {
  const state = createIssueState([
    { issueKey: 'issue::a', displayId: 'HIGH-1' },
  ])
  const next = updateIssueStatus(state, 'issue::a', 'accepted')
  assert.equal(next['issue::a'].status, 'accepted')
})
```

- [ ] **Step 2: Run the target test to verify it fails**

Run: `node --test tests/issueState.test.mjs`
Expected: FAIL because issue status helper does not exist.

- [ ] **Step 3: Implement local-only issue status state**

```javascript
export function updateIssueStatus(state, issueKey, status) {
  return {
    ...state,
    [issueKey]: { ...(state[issueKey] || {}), status },
  }
}
```

Supported values:
- `todo`
- `accepted`
- `ignored`
- `fixed_pending_verify`

- [ ] **Step 4: Expose status controls in the report**

Add issue-level chips/buttons:
- `待处理`
- `已采纳`
- `已忽略`
- `待复核`

Do not persist server-side. Keep this inside current browser session only.

- [ ] **Step 5: Re-run tests**

Run: `npm test`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add frontend/src/lib/issueState.js frontend/src/App.vue frontend/src/components/ReportViewer.vue frontend/tests/issueState.test.mjs frontend/tests/uiCopy.test.mjs
git commit -m "feat: add local issue status flow"
```

### Task 4: Export Accepted Suggestions

**Files:**
- Create: `frontend/src/lib/exportSuggestions.js`
- Modify: `frontend/src/App.vue`
- Modify: `frontend/src/components/ReportViewer.vue`
- Test: `frontend/tests/issueState.test.mjs`

- [ ] **Step 1: Write the failing export formatting test**

```javascript
test('buildSuggestionExport only includes accepted or pending-fix issues', () => {
  const markdown = buildSuggestionExport({
    issues: [
      { displayId: 'HIGH-1', title: '验收标准缺失', suggestion: '补充失败重试', status: 'accepted' },
      { displayId: 'LOW-1', title: '术语不统一', suggestion: '统一术语', status: 'ignored' },
    ],
  })
  assert.match(markdown, /HIGH-1/)
  assert.doesNotMatch(markdown, /LOW-1/)
})
```

- [ ] **Step 2: Run test to verify it fails**

Run: `node --test tests/issueState.test.mjs`
Expected: FAIL because export helper does not exist.

- [ ] **Step 3: Implement markdown export helper**

```javascript
export function buildSuggestionExport({ issues = [] }) {
  const included = issues.filter((issue) => ['accepted', 'fixed_pending_verify'].includes(issue.status))
  return included.map((issue) => `## ${issue.displayId} ${issue.title}\n- 建议：${issue.suggestion}`).join('\n\n')
}
```

- [ ] **Step 4: Add export trigger**

Add one report-level button:
- `导出修改建议`

Download as `.md`.

- [ ] **Step 5: Re-run frontend tests**

Run: `npm test`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add frontend/src/lib/exportSuggestions.js frontend/src/App.vue frontend/src/components/ReportViewer.vue frontend/tests/issueState.test.mjs
git commit -m "feat: export accepted suggestion list"
```

### Task 5: Assistant Recovery and More Reliable Issue Follow-Up

**Files:**
- Modify: `backend/services/chat_service.py`
- Modify: `frontend/src/components/AssistantPanel.vue`
- Modify: `frontend/src/App.vue`
- Test: `tests/test_chat_service.py`
- Test: `frontend/tests/assistantPanel.test.mjs`

- [ ] **Step 1: Write the failing backend retry-action test**

```python
def test_chat_response_marks_retry_action_on_model_error(self):
    result = build_chat_response(...)
    self.assertEqual(result["assistant_status"], "error")
    self.assertTrue(any(item["type"] == "retry_chat" for item in result["suggested_actions"]))
```

- [ ] **Step 2: Run target test to verify it fails**

Run: `python3 -m unittest -q tests.test_chat_service`
Expected: FAIL because assistant actions do not include retry-specific recovery.

- [ ] **Step 3: Implement retry-aware assistant fallback**

Rules:
- if model unavailable -> show `assistant_status=unavailable`
- if model error -> show `assistant_status=error` and include `retry_chat`
- if issue not resolved from prompt -> explicitly ask user to choose from current issue list instead of vague fallback text

- [ ] **Step 4: Wire frontend retry action**

When user clicks `retry_chat`, resend the latest user message once.

- [ ] **Step 5: Re-run tests**

Run:
- `python3 -m unittest -q tests.test_chat_service`
- `npm test`

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add backend/services/chat_service.py frontend/src/components/AssistantPanel.vue frontend/src/App.vue tests/test_chat_service.py frontend/tests/assistantPanel.test.mjs
git commit -m "feat: add single-run assistant recovery actions"
```

### Task 6: Direct Text Input Instead of File Upload

**Files:**
- Modify: `backend/api/schemas.py`
- Modify: `backend/api/routes.py`
- Modify: `backend/services/review_service.py`
- Modify: `frontend/src/components/UploadArea.vue`
- Modify: `frontend/src/App.vue`
- Modify: `frontend/src/lib/reviewApi.js`
- Test: `tests/test_chat_route.py` or add `tests/test_review_route.py`
- Test: `frontend/tests/reviewApi.test.mjs`

- [ ] **Step 1: Write the failing backend route test**

```python
def test_start_review_accepts_direct_text_payload(self):
    response = client.post("/api/review/start", json={
        "session_id": "session-1",
        "preset": "normal",
        "direct_text": "# PRD\n\n## 用户价值\n..."
    })
    self.assertEqual(response.status_code, 200)
```

- [ ] **Step 2: Run target test to verify it fails**

Run: `python3 -m unittest -q tests.test_review_route`
Expected: FAIL because the route only supports uploaded file sessions.

- [ ] **Step 3: Extend review input contract minimally**

Two allowed modes:
- uploaded file
- direct text

Keep them mutually exclusive.

- [ ] **Step 4: Update upload area UI**

Add a simple toggle:
- `上传文件`
- `直接粘贴`

The paste mode should use a large textarea and submit through the same review start flow.

- [ ] **Step 5: Re-run tests**

Run:
- `python3 -m unittest discover -q`
- `npm test`

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add backend/api/schemas.py backend/api/routes.py backend/services/review_service.py frontend/src/components/UploadArea.vue frontend/src/App.vue frontend/src/lib/reviewApi.js tests/test_review_route.py frontend/tests/reviewApi.test.mjs
git commit -m "feat: support direct text review input"
```

### Task 7: Modified Text Recheck in the Same Run

**Files:**
- Modify: `frontend/src/components/AssistantPanel.vue`
- Modify: `frontend/src/App.vue`
- Modify: `backend/services/chat_service.py`
- Optional Modify: `backend/api/routes.py`
- Test: `tests/test_chat_service.py`
- Test: `frontend/tests/assistantPanel.test.mjs`

- [ ] **Step 1: Write the failing behavior test**

```python
def test_chat_service_can_compare_issue_against_revised_text(self):
    result = build_chat_response(
        session=session,
        message="请判断下面修改后文本是否解决 HIGH-1：\\n验收标准补充了失败重试...",
        selected_issue_id="HIGH-1",
    )
    self.assertIn("是否解决", result["message"])
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest -q tests.test_chat_service`
Expected: FAIL because there is no explicit modified-text recheck mode.

- [ ] **Step 3: Add a minimal recheck mode**

Rules:
- user supplies revised text in chat
- assistant evaluates only against currently focused issue
- answer in one of three buckets:
  - `已明显覆盖`
  - `部分覆盖，仍缺失`
  - `无法判断`

This should be single-run only. No diff engine required.

- [ ] **Step 4: Add one explicit UI shortcut**

Starter prompt:
- `判断修改后是否已解决`

- [ ] **Step 5: Re-run tests**

Run:
- `python3 -m unittest -q tests.test_chat_service`
- `npm test`

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add backend/services/chat_service.py frontend/src/components/AssistantPanel.vue frontend/src/App.vue tests/test_chat_service.py frontend/tests/assistantPanel.test.mjs
git commit -m "feat: add same-run revised text recheck"
```

---

## Delivery Order

**P0 first**
1. Task 1: Evidence Chain Contract
2. Task 2: Frontend Evidence Rendering and Source Jump
3. Task 3: Local Issue Status Flow
4. Task 4: Export Accepted Suggestions
5. Task 5: Assistant Recovery and More Reliable Issue Follow-Up

**P1 next**
6. Task 6: Direct Text Input Instead of File Upload
7. Task 7: Modified Text Recheck in the Same Run

---

## Verification Checklist

- Backend:
  - `python3 -m unittest discover -q`
- Frontend:
  - `npm test`
  - `npm run build`
- Manual:
  - Upload a PRD and complete one run
  - Verify each issue shows evidence snippet
  - Change issue status locally and export accepted suggestions
  - Ask the assistant to switch issue focus and retry after a forced failure
  - Return to report from assistant page without triggering a new review
  - Paste direct text and run a review
  - Paste revised text for one issue and verify recheck output

---

## Self-Review

**Spec coverage**
- Covers the single-run P0 items:
  - evidence chain
  - issue status flow
  - exportable suggestions
  - stronger assistant follow-up
  - retry / recovery
- Covers the selected single-run P1 items:
  - direct text input
  - revised text recheck
- Explicitly excludes history/workspace/team features.

**Placeholder scan**
- No `TODO` / `TBD`
- Each task has exact files, tests, commands, and commit points

**Type consistency**
- Uses `issue_key`, `display_id`, `source_quote`, `source_section`, `source_locator` consistently
- Uses local issue statuses consistently as `todo`, `accepted`, `ignored`, `fixed_pending_verify`

