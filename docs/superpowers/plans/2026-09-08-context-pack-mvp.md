# Context Pack MVP Sprint Plan

## Sprint goal

Ship a context-aware PRD review that can use explicit product background while preserving the existing stateless BYOK deployment and evidence traceability.

## Capacity

- Duration: one focused implementation iteration
- Team: one developer with Codex support
- Capacity: 13 points
- Committed: 11 points
- Buffer: 2 points for provider/prompt regressions and responsive UI fixes

## Committed stories

1. Product Context schema and browser persistence — 2 points
   - Product overview, business goals, target users, success metrics, and historical decisions/constraints.
   - Plaintext local browser persistence with explicit disclosure and a clear action.
2. Context editor in the workbench — 3 points
   - Enable/disable the pack per review without deleting it.
   - Show completion count and total character budget.
   - Match the existing warm editorial UI and mobile breakpoints.
3. Stateless request and backend validation — 2 points
   - Send enabled context in the existing multipart review request.
   - Reject malformed, oversized, or control-character content before model calls.
4. Context-aware prompts and evidence provenance — 3 points
   - Keep PRD and product context in distinct prompt sections.
   - Require every quoted issue to identify `prd` or a known context source.
   - Remove unverifiable quotes and surface source badges in the report.
5. Regression tests, documentation, push, and production deployment — 1 point

## Dependencies and critical path

Schema/storage -> editor/request contract -> prompt/evidence validation -> report rendering -> regression and production smoke tests.

No external database, identity provider, connector, vector store, or analytics service is required.

## Acceptance criteria

- An empty or disabled Context Pack produces the existing PRD-only request and report behavior.
- Context survives browser refresh but never enters server-side storage, cookies, repository files, or logs.
- The user can disable Context for a no-context comparison without deleting saved fields.
- The backend accepts at most 20,000 context characters across five fixed source types.
- All six reviewers receive the same validated context block.
- A quoted issue is retained only when its quote exists in the declared PRD/context source.
- The report labels evidence as `PRD 原文` or the concrete Context source.
- Backend, frontend, skill, build, audit, and production smoke suites pass.

## Risks and mitigations

- Prompt size and cost growth -> fixed field budgets, live character count, no historical file ingestion in this iteration.
- Context overrides the current PRD -> explicit prompt hierarchy and source typing.
- Stale or wrong context -> visible enable switch, editable fields, no autonomous memory writes.
- Privacy regression -> local-only persistence disclosure and stateless backend contract.
- Scope expansion into enterprise RAG -> connectors, ACL, embeddings, accounts, and automatic evolution remain out of scope.
