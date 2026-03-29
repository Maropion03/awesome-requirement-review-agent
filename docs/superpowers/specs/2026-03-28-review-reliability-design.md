# PRD Review Reliability Upgrade Design

- Date: 2026-03-28
- Status: Proposed (User-Approved for planning)
- Owner: Core backend (`backend/`)
- Scope: Reliability-focused optimization for review conclusion stability and output schema stability

## 1. Background

The repository already contains a PRD review backend (`FastAPI + SSE + LLM`) and a local rule-based skill (`skill-for-agent`).  
Current product goal for this iteration is **review reliability first**, with two hard constraints:

1. Conclusion drift is unacceptable: repeated runs on the same PRD should not frequently produce conflicting recommendations.
2. Output format instability is unacceptable: frontend/API consumers must always receive schema-stable payloads.

This design intentionally deprioritizes feature expansion and UI work.

## 2. Goals and Non-Goals

## 2.1 Goals

1. Guarantee schema-stable API/SSE output even under model failure.
2. Reduce recommendation and score drift without introducing high latency/cost.
3. Add traceability to explain why two runs differ (when they do).
4. Keep migration incremental and backward compatible.

## 2.2 Non-Goals

1. Rewriting the system into a fully rule-based engine.
2. Building a new frontend in this phase.
3. Multi-model voting or heavy ensemble orchestration.

## 3. Option Comparison

## 3.1 Option A: Lightweight constraints only

- Add strict schema validation and repair retries.
- Pros: fastest delivery, smallest code changes.
- Cons: format improves, drift reduction is limited.

## 3.2 Option B: Two-stage verification (Recommended)

- Primary review pass + secondary lightweight verifier.
- Verifier checks structure, evidence binding, score/recommendation consistency.
- Pros: balanced reliability/cost/latency; directly targets both red lines.
- Cons: pipeline becomes longer and requires run-level orchestration.

## 3.3 Option C: Rule-first scoring

- Rule engine drives score/recommendation; LLM adds narrative.
- Pros: strongest determinism.
- Cons: weaker semantic coverage for nuanced PRDs; bigger product behavior shift.

## 3.4 Decision

Adopt **Option B: Two-stage verification**.

## 4. High-Level Architecture

## 4.1 Current (Simplified)

`upload -> parse -> dimension LLM reviews -> report -> SSE complete`

## 4.2 Target (Reliability Pipeline)

`upload -> parse -> primary review -> normalize/validate -> secondary verify -> report finalize -> persist run artifacts -> SSE complete`

Key additions:

1. Contract Layer (`ReviewResult v1`, `SSE Envelope v1`)
2. Verification Layer (consistency/evidence/score checks)
3. Run Context (`run_id`, idempotency, trace artifacts)
4. Degradation Path (schema-safe fallback output)

## 5. Contract Stability Design

## 5.1 Canonical report contract (`ReviewResult v1`)

- Strongly typed payload with required keys and enums.
- Every public endpoint returns this contract or a degraded variant of the same contract.
- Include explicit metadata:
  - `schema_version`
  - `run_id`
  - `status` (`completed` | `degraded_complete`)
  - `degraded_reason` (nullable)

## 5.2 Processing chain

All LLM-derived payloads pass:

1. `strict_parse`
2. `normalize`
3. `validate_schema`
4. `repair_retry` (max 2, structure-only)

If still invalid:

- Return deterministic degraded skeleton with stable shape.
- Never leak raw exception shape to API consumers.

## 5.3 Versioned SSE envelope

Every SSE event shape:

`{ event_type, schema_version, session_id, run_id, ts, payload }`

This prevents frontend crashes due to ad-hoc event payload drift.

## 6. Conclusion Drift Control Design

## 6.1 Primary pass

- Keep existing single-pass review as the first stage.
- Lock generation parameters (`temperature`, `top_p`, prompt version) to reduce randomness.

## 6.2 Secondary verifier (lightweight)

Verifier does not rewrite the whole report. It only checks:

1. Structural consistency (`score/issues/recommendation` coherence)
2. Evidence binding for each issue (`section/location/snippet` requirements)
3. Score normalization and recommendation threshold consistency

Critical dimensions for second-check:

- `completeness`
- `feasibility`
- `risk`

Non-critical dimensions only receive structure and consistency checks.

## 6.3 Reliability signals exposed to client

Per dimension include:

- `confidence` (0-1)
- `evidence_count`

This makes uncertainty visible instead of hidden.

## 7. Data Flow, Idempotency, and Failure Model

## 7.1 Run lifecycle

State machine:

`RECEIVED -> PARSED -> REVIEWED -> VERIFIED -> REPORTED -> COMPLETED`

Error path:

`... -> DEGRADED_COMPLETE` (schema-safe output guaranteed)

## 7.2 Idempotency model

- Each start request creates or reuses a `run_id`.
- Same `session_id` + same parameters returns the same in-flight/completed `run_id` rather than launching duplicate runs.
- All logs/events/reports keyed by `run_id`.

## 7.3 Failure classes

1. Recoverable (parse/shape mismatch): repair retries.
2. Non-recoverable (timeout/provider outage): degraded completion.
3. Unexpected exceptions: mapped to stable contract + internal trace.

## 8. Validation and Acceptance Criteria

## 8.1 Format stability

1. `schema_valid_rate = 100%` for 500 continuous runs (report + SSE envelope).
2. No frontend parse/runtime crash caused by missing/renamed fields.

## 8.2 Drift control

On repeated runs of the same PRD (n=10):

1. Recommendation consistency >= 95%
2. Total score standard deviation <= 0.35
3. High-severity issue overlap >= 85%

Metrics are tracked per preset (`normal`, `p0_critical`, `innovation`).

## 8.3 Evidence quality

1. Overall `issue_evidence_coverage >= 95%`
2. High-severity issue evidence coverage = 100%

## 8.4 Runtime stability

1. 5xx rate < 0.5%
2. Idempotency correctness = 100%
3. SSE reconnection success >= 99%

## 9. Rollout Plan (3 Iterations)

## 9.1 Iteration 1: Contract stability foundation

1. Introduce canonical schema and SSE envelope versioning.
2. Add parse/normalize/validate/repair chain.
3. Add degraded skeleton completion path.
4. Keep backward-compat fields during transition.

Deliverable: format stability gate green.

## 9.2 Iteration 2: Drift control

1. Add secondary verifier for key dimensions.
2. Enforce evidence binding checks.
3. Lock model parameters and prompt versioning.
4. Add score normalization + recommendation consistency checks.

Deliverable: drift KPIs meet thresholds.

## 9.3 Iteration 3: Observability and idempotency hardening

1. Implement run-level idempotent start behavior.
2. Persist run artifacts for forensic trace.
3. Add benchmark suite + CI reliability gate.

Deliverable: stable operation under repeated/concurrent use.

## 10. Risks and Mitigations

1. Risk: Added pipeline latency from verification stage.
   - Mitigation: verifier is narrow and lightweight; only deep-check 3 key dimensions.
2. Risk: Over-constraining output may suppress useful nuance.
   - Mitigation: apply strictness to schema and consistency, not narrative richness.
3. Risk: Migration breaks existing frontend assumptions.
   - Mitigation: temporary dual-field compatibility and explicit schema versioning.

## 11. Implementation Notes

Likely affected modules:

1. `backend/api/schemas.py`
2. `backend/services/review_service.py`
3. `backend/services/sse_service.py`
4. `backend/api/routes.py`
5. `backend/config/prompts.py` (prompt version pinning)

Deferred for this phase:

1. `skill-for-agent` deep refactor
2. frontend redesign

## 12. Definition of Done

This design is considered implemented when:

1. All acceptance metrics in Section 8 pass on a fixed benchmark set.
2. Reliability pipeline is default path.
3. Degraded mode still returns schema-valid payloads.
4. Run traceability (`run_id`) is available end-to-end.
