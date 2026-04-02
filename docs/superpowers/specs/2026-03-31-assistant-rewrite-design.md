# PRD 评审助手重构设计

- Date: 2026-03-31
- Status: Proposed
- Owner: Frontend + backend integration
- Scope: Rework the assistant area so issue focus is stable and personalized replies only appear when the model is actually available

## 1. Background

The current PRD review workstation already supports upload, review, report rendering, and a guided assistant panel. The workflow is usable, but the assistant experience is still brittle:

1. Issue focus is not stable enough for the user. In practice it can appear to lock onto the first high-severity item or lose alignment when the user switches between report and assistant views.
2. Personalized replies are inconsistent. When the model path is not actually available, the assistant often falls back to a generic sentence instead of making the failure explicit.
3. The current assistant UI mixes three responsibilities in one place:
   - issue focus
   - model availability
   - chat interaction

This makes the board feel rigid. The user intent for this iteration is not a full product rewrite. The goal is to make the assistant feel precise and trustworthy while preserving the existing review pipeline.

## 2. Goals and Non-Goals

## 2.1 Goals

1. Let the assistant reliably focus the same issue that the report page shows.
2. Allow users to switch to a specific issue by clicking it or by naming it in the prompt.
3. Produce personalized answers only when the model is available and responding successfully.
4. Make model unavailability explicit instead of silently returning a generic answer.
5. Keep the current report page and review pipeline intact.

## 2.2 Non-Goals

1. Replacing the existing review workflow with a separate chat-first application.
2. Introducing a second model fallback that fabricates personalized text without model support.
3. Reworking the scoring engine or review agent logic in the same iteration.
4. Expanding guided actions into arbitrary tool execution.

## 3. Options

## 3.1 Option A: Minimal prompt and parser patch

Only improve the backend prompt and issue parsing.

Pros:

1. Fastest path.
2. Smallest code change.

Cons:

1. Issue focus still depends on weak identifiers.
2. When model availability is poor, the UI still feels ambiguous.
3. The assistant board remains structurally rigid.

## 3.2 Option B: Structured assistant refactor with stable issue identity

Split the assistant into three clear responsibilities:

1. Stable issue focus
2. Explicit model status
3. Personalized chat generation

Pros:

1. Fixes the issue selection problem and the personalization problem together.
2. Keeps the current page structure mostly intact.
3. Makes future assistant improvements easier.

Cons:

1. More work than a simple patch.
2. Requires backend and frontend contract updates.

## 3.3 Option C: Dedicated assistant page

Move the assistant into a separate page and redesign the interaction model entirely.

Pros:

1. Strongest separation of concerns.
2. Cleanest long-term layout.

Cons:

1. Too much scope for the current iteration.
2. Would delay solving the current issue-focus and model-personalization problems.

## 3.4 Decision

Adopt **Option B**.

## 4. Target Architecture

The refactor should treat the assistant as a small system with three layers:

1. Issue identity layer
2. Assistant state and routing layer
3. Response rendering layer

### 4.1 Issue identity layer

Each issue should carry two identifiers:

1. `display_id`
   - Human-readable label shown in the UI.
   - Examples: `HIGH-1`, `HIGH-2`, `MEDIUM-1`.

2. `issue_key`
   - Stable internal identity for the current report snapshot.
   - Used to keep the report page and assistant page aligned.

`display_id` can still be regenerated when issues are sorted or renumbered. `issue_key` is what the assistant should use for stable focus within a report session.

### 4.2 Assistant state and routing layer

The assistant should resolve the active issue in this order:

1. Explicit issue selected from the report page.
2. Issue key or display id parsed from the user prompt.
3. Title or keyword match in the user prompt.
4. No issue focus, if none of the above matches.

The assistant state should explicitly track:

1. The current report snapshot.
2. The currently focused issue.
3. Whether the model is available.
4. The last response mode (`model`, `unavailable`, or `error`).

### 4.3 Response rendering layer

The assistant response should not pretend that a generic sentence is a personalized answer.

Instead:

1. If the model is available and returns valid structured content, render that personalized response.
2. If the model is unavailable, return a clear unavailable state.
3. If the model response is malformed, surface an error state and keep the current report usable.

## 5. User Experience Design

## 5.1 Assistant page structure

The assistant area should be reorganized into three visible zones:

1. Issue dock
   - Shows the issues from the current report.
   - Clicking an issue focuses it.
   - The focused issue stays visible as context.

2. Model status bar
   - Shows whether the model is connected, unavailable, or currently responding.
   - Prevents the user from mistaking fallback text for a personalized answer.

3. Conversation area
   - Shows chat messages.
   - Accepts typed prompts.
   - Shows guided action chips only when they are relevant.

## 5.2 Issue focus behavior

Issue focus should behave consistently across the report page and assistant page:

1. Clicking an issue card in the report page should update the assistant focus state.
2. Clicking a source reference inside the assistant should focus the same issue.
3. Typing a prompt like `HIGH-2 具体有什么问题` or `请围绕问题「...」给出修改建议` should resolve to the matching issue when possible.
4. The assistant should never silently jump to the first high-severity issue just because the identifier was incomplete.

## 5.3 Personalized reply behavior

When the model is available:

1. “解释当前结论” should yield a report-aware explanation.
2. “给我修改建议” should yield issue-specific or report-specific advice.
3. “这个问题具体有什么问题” should explain the selected issue using its severity, dimension, and description.

When the model is not available:

1. The UI should clearly show that the assistant is unavailable.
2. The system should not emit a fake personalized answer.
3. The report page should remain usable.

## 6. Backend Design

## 6.1 Issue key generation

At report finalization time, each issue should be decorated with:

1. `display_id`
2. `issue_key`

Recommended approach:

1. Keep the current severity-based global renumbering for `display_id`.
2. Generate `issue_key` from the report snapshot and issue fingerprint so the same issue can be matched reliably within the report session.

The exact fingerprint can use:

1. severity
2. dimension
3. title
4. description
5. suggestion

This preserves readability while giving the assistant a stable internal reference.

## 6.2 Issue resolution

The chat service should resolve issue context using a small deterministic matcher:

1. Direct `issue_key` match.
2. Direct `display_id` match.
3. Title substring match.
4. Keyword-based fallback from prompt text.

If none match, the assistant should answer at the report level rather than inventing a specific issue.

## 6.3 Model availability contract

The assistant backend should make model status explicit:

1. `available`
2. `unavailable`
3. `error`

Rules:

1. If configuration does not provide a usable key, the backend should return `unavailable`.
2. If the model call fails or returns malformed content, the backend should return `error`.
3. Only successful structured model output should be rendered as a personalized answer.

This replaces the current pattern of silently using a generic sentence as if it were personalized output.

## 6.4 Chat response shape

The assistant response should include:

```json
{
  "message": "模型生成的个性化回答，或者明确的状态提示",
  "response_mode": "model",
  "assistant_status": "available",
  "selected_issue": {
    "issue_key": "issue-abc123",
    "display_id": "HIGH-2",
    "title": "缺失功能交互流程的完整描述"
  },
  "suggested_actions": [],
  "source_refs": [],
  "run_state": {}
}
```

`response_mode` should be one of:

1. `model`
2. `unavailable`
3. `error`
4. `report_level`

## 7. Frontend Design

## 7.1 State model

The frontend should keep the following as first-class state:

1. current report snapshot
2. currently focused issue
3. assistant status
4. selected issue source refs
5. chat history

The selected issue should be stored as a structured object, not only as `HIGH-1`.

## 7.2 Report-to-assistant handoff

When the user leaves the report page and enters the assistant page:

1. Preserve the focused issue object.
2. Preserve the report snapshot.
3. Preserve the stable issue key if available.
4. Restore the same issue context after refresh when the session is still valid.

## 7.3 UI changes

The assistant page should show:

1. A focused issue dock that makes it obvious which issue is active.
2. A model status badge so users can see whether personalized replies are expected.
3. A conversation composer that accepts free-form prompts.
4. Quick actions only when they fit the current context.

The UI should no longer imply that the assistant is always capable of personalizing a response.

## 8. Error Handling

1. If a selected issue no longer exists after a re-review, the UI should mark the context as stale and prompt the user to reselect.
2. If the model is unavailable, the assistant should say so explicitly.
3. If the chat response is malformed, the assistant should preserve the current thread and show an error state.
4. If the user references an unknown issue id in the prompt, the assistant should fall back to report-level reasoning instead of picking the wrong issue.

## 9. Testing Strategy

## 9.1 Backend tests

1. Issue resolution should prefer explicit issue key over display id and title match.
2. Model unavailable should produce a stable explicit status.
3. Personalized model output should still round-trip through the structured response contract.

## 9.2 Frontend tests

1. Clicking an issue on the report page updates the assistant focus state.
2. Typing a prompt with a specific issue id resolves to the correct focused issue.
3. The assistant status badge changes when the backend reports unavailable or error.
4. A stale issue selection is clearly marked instead of silently falling back to `HIGH-1`.

## 10. Acceptance Criteria

This design is considered complete when:

1. The report page can select any issue and the assistant page stays aligned with it.
2. The assistant can resolve issue-specific prompts beyond the first high-priority item.
3. Personalized replies only appear when the model is actually available.
4. Model-unavailable cases are explicit and no longer masquerade as valid answers.
5. The existing review pipeline and report UI remain intact.

