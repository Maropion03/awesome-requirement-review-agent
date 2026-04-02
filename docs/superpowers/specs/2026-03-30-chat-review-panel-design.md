# PRD 评审工作台对话式助手设计

- Date: 2026-03-30
- Status: Proposed
- Owner: Frontend + backend integration
- Scope: In-place upgrade of the current review workstation with a right-side guided chat assistant

## 1. Background

The repository already has a working PRD review flow:

- Upload PRD
- Start review
- Stream progress through SSE
- Render the final report

The current UI is functional, but it is still task-oriented rather than conversational. The product owner wants the review experience to feel like a guided assistant: users should be able to read the report, ask follow-up questions, and trigger a small set of actions without leaving the page.

This iteration focuses on **making the review interface conversational** without changing the core review pipeline.

## 2. Goals and Non-Goals

## 2.1 Goals

1. Add a persistent right-side chat panel to the existing workstation layout.
2. Let the assistant explain review outcomes in plain language.
3. Let the assistant reference the current report, the original PRD, and the current run state.
4. Support a limited set of guided actions from chat, such as rerun, preset switch, and issue focus.
5. Keep the existing report and progress views intact.

## 2.2 Non-Goals

1. Replacing the current review workflow with a pure chat-only flow.
2. Rebuilding the whole frontend into a new agent console.
3. Adding free-form tool execution beyond the agreed guided actions.
4. Changing the core review scoring logic in the same iteration.

## 3. Decision Summary

## 3.1 Chosen Layout

Use a **right-side fixed chat panel** next to the current workstation content.

Why:

1. The report remains visible while the user chats.
2. It matches the current workflow of "read result, ask follow-up, inspect source".
3. It supports guided assistant behavior without making the page feel modal or fragmented.

## 3.2 Assistant Style

Use a **guided assistant** style.

Behavior:

1. Explain the result first.
2. Offer the next best action.
3. Surface source references when available.
4. Suggest actions instead of silently executing everything.

## 3.3 Context Scope

The assistant may see:

1. The current review report.
2. The original PRD content or a relevant excerpt.
3. The current run state and issue list.

This is enough to answer "why", "where", and "what should I change" without introducing extra data sources.

## 4. Proposed UX

## 4.1 Page Layout

The page is split into two zones:

1. Main workstation area
   - Upload area
   - Preset selector
   - Progress view
   - Final report

2. Right-side assistant panel
   - Conversation history
   - Suggested actions
   - Context snapshot

The assistant panel stays visible during the whole session.

## 4.2 Chat Panel Sections

The chat panel should contain three blocks:

1. Conversation feed
   - User questions
   - Assistant answers
   - System status messages

2. Quick actions
   - Rerun review
   - Switch preset
   - Jump to an issue
   - Generate rewrite suggestion

3. Context summary
   - Current report score and recommendation
   - Current run status
   - Selected issue
   - Short PRD excerpt when relevant

## 4.3 Interaction Rules

1. When a user asks "why is this issue high priority", the assistant should explain the reason and link back to the relevant issue.
2. When a user asks "show me where this comes from", the assistant should surface the source excerpt.
3. When a user asks for an action, the assistant should confirm the action before executing it.
4. When the review is still running, the assistant should be able to summarize progress and current findings.
5. The assistant should remain helpful but not chatty by default.

## 5. Backend Design

## 5.1 Chat API

Add a lightweight chat endpoint that accepts:

- `session_id`
- `message`
- optional `selected_issue_id`
- optional `context_mode`

The endpoint returns a structured response:

- `message`: assistant response text
- `suggested_actions`: array of actionable buttons
- `source_refs`: issue IDs or PRD section references
- `target_issue_id`: optional issue focus target
- `run_state`: current review state summary

## 5.2 Response Shape

The assistant response should be stable and UI-friendly. A minimal shape is:

```json
{
  "message": "The issue is marked high because...",
  "suggested_actions": [
    {"type": "rerun", "label": "重新评审"},
    {"type": "switch_preset", "label": "切换到 P0"}
  ],
  "source_refs": [
    {"type": "issue", "id": "[高-1]"},
    {"type": "section", "name": "验收标准"}
  ],
  "target_issue_id": "[高-1]"
}
```

## 5.3 Action Handling

The initial action set is intentionally small:

1. `rerun`
2. `switch_preset`
3. `focus_issue`
4. `generate_suggestion`

These actions should map onto existing review state or lightweight frontend behavior. They should not require a new orchestration engine in this iteration.

## 5.4 Context Assembly

When generating a chat response, the backend should assemble a compact context bundle:

1. Current report summary
2. Current run status
3. Optional issue details
4. Optional PRD excerpt

The context should be narrow enough to keep replies stable and fast.

## 6. Frontend Design

## 6.1 Component Split

Suggested components:

1. `AssistantPanel`
   - Container for the whole chat area

2. `ChatThread`
   - Conversation history

3. `ChatComposer`
   - Input box and send button

4. `ActionChips`
   - Quick action buttons

5. `ContextSnapshot`
   - Current score, recommendation, selected issue

6. `SourcePreview`
   - PRD excerpt or issue reference preview

## 6.2 Layout Behavior

1. Desktop: two-column layout with fixed-width assistant panel.
2. Tablet: assistant panel collapses into a drawer or stacked region.
3. Mobile: assistant panel becomes a bottom sheet or tabbed section.

## 6.3 User Flow

1. User uploads a PRD.
2. Review starts and progress appears in the main area.
3. Assistant explains the ongoing result in the right panel.
4. User asks a question or clicks an action chip.
5. Assistant responds with explanation and optionally triggers a guided action.
6. The report remains visible throughout.

## 7. Data Model

## 7.1 Chat Message Model

Each message should include:

- `role`: `user | assistant | system`
- `content`
- `timestamp`
- `related_issue_id`
- `source_refs`
- `actions`

## 7.2 Assistant State Model

The frontend should keep:

- `session_id`
- `selected_issue_id`
- `chat_history`
- `current_context`
- `pending_action`

## 8. Error Handling

1. If the assistant cannot find enough context, it should say so and suggest the closest available reference.
2. If the chat endpoint fails, the UI should keep the report usable and show a retry affordance.
3. If an action cannot be executed, the assistant should explain why and stay in the current session.
4. If the review is incomplete, the assistant should clearly distinguish "running" from "completed".

## 9. Testing Strategy

## 9.1 Frontend Tests

1. The assistant panel renders alongside the existing workstation.
2. Message submission updates the thread.
3. Quick action buttons trigger the correct local behavior.
4. A selected issue updates the context snapshot.

## 9.2 Backend Tests

1. Chat response shape is stable.
2. Context assembly includes report, issue, and PRD excerpt data as expected.
3. Action mapping is deterministic.
4. Error responses remain schema-safe.

## 10. Rollout Plan

## 10.1 Phase 1: Layout and static chat shell

1. Add the right-side panel.
2. Render a static conversation mock.
3. Wire the panel to current report state.

## 10.2 Phase 2: Context-aware chat replies

1. Add chat request/response handling.
2. Provide report and issue context.
3. Render source references.

## 10.3 Phase 3: Guided actions

1. Add rerun and preset switch actions.
2. Add issue focus and suggestion generation.
3. Keep action confirmation visible in chat.

## 11. Definition of Done

This design is complete when:

1. The workstation still works as before.
2. A right-side chat panel is visible on desktop.
3. The assistant can explain results using current report and PRD context.
4. At least one guided action can be triggered from the chat panel.
5. The implementation stays backward compatible with the current review flow.
