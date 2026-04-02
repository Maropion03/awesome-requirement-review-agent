# Static Single-Page Review Shell Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Merge the existing `first / second / third` static review mockups into one same-page shell that switches views without URL navigation and talks to the current backend API.

**Architecture:** Keep the static HTML delivery model. Use `frontend/first page code_integrated.html` as the single shell, embed workbench/report/assistant panels inside it, and centralize runtime state in one in-page store plus `sessionStorage` for refresh recovery. Reuse the existing backend endpoints for upload, start, SSE, report fetch, chat, reset, share, and PDF export.

**Tech Stack:** Static HTML, Tailwind CDN, vanilla JavaScript, FastAPI backend, Node test runner.

---

## File Structure

- `frontend/first page code_integrated.html`
  Responsibility: single-page shell, shared layout, navigation button switching, upload/start/stream/report/chat integration.
- `frontend/tests/staticSinglePageShell.test.mjs`
  Responsibility: assert the shell is same-page, exposes all three view containers, and targets the current backend API.
- `docs/superpowers/plans/2026-04-02-static-single-page-shell.md`
  Responsibility: execution handoff for this static-shell integration.

### Task 1: Lock Same-Page Requirements With Tests

**Files:**
- Create: `frontend/tests/staticSinglePageShell.test.mjs`
- Modify: `frontend/package.json` (only if test discovery needs adjustment; avoid unless necessary)

- [ ] **Step 1: Write the failing test for same-page views**

```javascript
import test from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'

const source = readFileSync(resolve(process.cwd(), 'first page code_integrated.html'), 'utf8')

test('static shell keeps workbench report and assistant in one page', () => {
  assert.match(source, /id="workbenchView"/)
  assert.match(source, /id="reportView"/)
  assert.match(source, /id="assistantView"/)
  assert.match(source, /function switchView\(/)
})
```

- [ ] **Step 2: Write the failing test for no URL jumps and correct backend target**

```javascript
test('static shell avoids page redirects and talks to backend 8005', () => {
  assert.doesNotMatch(source, /window\.location\.href/)
  assert.match(source, /127\.0\.0\.1:8005\/api/)
  assert.match(source, /\/review\/report\//)
  assert.match(source, /\/review\/chat/)
})
```

- [ ] **Step 3: Run the test to verify it fails**

Run: `node --test tests/staticSinglePageShell.test.mjs`
Expected: FAIL because the current file still contains URL navigation and does not expose three in-page view containers.

### Task 2: Replace Multi-Page Navigation With One Shared Shell

**Files:**
- Modify: `frontend/first page code_integrated.html`
- Reference only: `frontend/second page/second_page_integrated.html`
- Reference only: `frontend/third page/third_page_integrated.html`

- [ ] **Step 1: Build one shared layout with three in-page view containers**

Create three top-level sections in the single file:
- `#workbenchView`
- `#reportView`
- `#assistantView`

Keep the current left navigation chrome, but replace link redirects with:

```javascript
function switchView(viewName) {
  activeView = viewName
  document.querySelectorAll('[data-view]').forEach((section) => {
    section.style.display = section.id === `${viewName}View` ? '' : 'none'
  })
}
```

- [ ] **Step 2: Centralize runtime state**

Add one state object in the page:

```javascript
const appState = {
  sessionId: null,
  preset: 'normal',
  report: null,
  reviewStatus: 'ready',
  selectedIssueId: null,
  conversationHistory: [],
}
```

Persist and hydrate:

```javascript
function persistState() {
  sessionStorage.setItem('singlePageReviewState', JSON.stringify(appState))
}
```

- [ ] **Step 3: Rewire upload/start/SSE to update same-page state**

Reuse the existing workbench behavior, but on complete:

```javascript
appState.report = data
appState.reviewStatus = 'completed'
persistState()
renderReport(data)
renderAssistantContext()
switchView('report')
```

- [ ] **Step 4: Rewire report interactions to stay in-page**

When an issue card is selected:

```javascript
function focusIssue(issue) {
  appState.selectedIssueId = issue.issue_key || issue.display_id || issue.id || null
  persistState()
  renderAssistantContext()
  switchView('assistant')
}
```

- [ ] **Step 5: Rewire assistant actions to same-page state**

Keep `/review/chat`, but stop clearing context by page jump. For rerun:

```javascript
async function handleRerun() {
  if (!appState.sessionId) return
  await fetch(`${API_BASE}/review/reset?session_id=${appState.sessionId}`, { method: 'POST' })
  resetReviewState()
  switchView('workbench')
}
```

### Task 3: Refresh-Safe Fetching and View Rendering

**Files:**
- Modify: `frontend/first page code_integrated.html`

- [ ] **Step 1: Add report hydration for refresh**

```javascript
async function ensureReportLoaded() {
  if (appState.report || !appState.sessionId) return appState.report
  const response = await fetch(`${API_BASE}/review/report/${appState.sessionId}`)
  if (!response.ok) return null
  appState.report = await response.json()
  persistState()
  return appState.report
}
```

- [ ] **Step 2: Render assistant summary from shared state**

Use the same report data for:
- score
- recommendation
- current session status
- selected issue context

- [ ] **Step 3: Keep export/share/pdf behavior on the same shell**

Continue using:
- `POST /review/share?session_id=...`
- `GET /review/export/pdf/{session_id}`

No URL navigation should happen for these operations.

### Task 4: Verify the Single-Page Shell

**Files:**
- Test: `frontend/tests/staticSinglePageShell.test.mjs`
- Verify: `frontend/first page code_integrated.html`

- [ ] **Step 1: Run the targeted test**

Run: `node --test tests/staticSinglePageShell.test.mjs`
Expected: PASS.

- [ ] **Step 2: Run the full frontend test suite**

Run: `npm test`
Expected: PASS.

- [ ] **Step 3: Run the frontend build**

Run: `npm run build`
Expected: PASS.

- [ ] **Step 4: Manually verify via the dev server**

Open the static page in the browser and verify:
- uploading a file keeps the user on one page
- review completion switches to the report view without URL change
- clicking an issue switches to the assistant view without URL change
- assistant chat calls the backend successfully

