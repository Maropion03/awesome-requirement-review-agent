# Review Reliability Upgrade Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make PRD review results stable and schema-safe by implementing a two-stage reliability pipeline with versioned SSE events, verifier checks, degraded fallback responses, and run-level traceability.

**Architecture:** Keep the existing upload/start/stream/report flow, but insert a strict contract layer (`parse -> normalize -> validate -> repair`) and a lightweight secondary verifier for key dimensions. Introduce `run_id`-based lifecycle management and versioned SSE event envelopes so all clients receive deterministic payload shapes. Persist run artifacts for debugging and drift analysis without changing the core product surface.

**Tech Stack:** Python 3.11, FastAPI, Pydantic v2, sse-starlette, unittest, aiofiles/json

---

Spec reference: `docs/superpowers/specs/2026-03-28-review-reliability-design.md`

### Planned File Structure

- Create: `backend/contracts/review_result.py`  
  Responsibility: canonical schema contract for API report + degraded report + SSE envelope metadata.
- Create: `backend/services/result_pipeline.py`  
  Responsibility: strict parse, normalize, validate, repair retry for LLM payloads.
- Create: `backend/services/verification_service.py`  
  Responsibility: secondary checks (consistency, evidence binding, score/recommendation coherence).
- Create: `backend/services/run_registry.py`  
  Responsibility: `run_id` allocation, idempotent run lookup, lifecycle state transitions.
- Create: `backend/services/run_artifact_store.py`  
  Responsibility: persist final report, verifier summary, and run metadata.
- Modify: `backend/api/schemas.py`  
  Responsibility: align response models with canonical contract and include `run_id/schema_version/status`.
- Modify: `backend/api/routes.py`  
  Responsibility: idempotent start behavior and run-aware responses.
- Modify: `backend/services/review_service.py`  
  Responsibility: orchestrate primary pass + result pipeline + verifier + degrade fallback.
- Modify: `backend/services/sse_service.py`  
  Responsibility: versioned SSE envelope.
- Modify: `backend/config/prompts.py`  
  Responsibility: pin prompt version metadata used in runs.
- Create: `backend/tests/test_review_contract.py`
- Create: `backend/tests/test_result_pipeline.py`
- Create: `backend/tests/test_verification_service.py`
- Create: `backend/tests/test_run_registry.py`
- Create: `backend/tests/test_sse_envelope.py`
- Create: `backend/tests/test_review_service_reliability.py`
- Create: `backend/tests/test_routes_idempotency.py`

### Task 1: Canonical Contract Foundation

**Files:**
- Create: `backend/contracts/review_result.py`
- Modify: `backend/api/schemas.py`
- Test: `backend/tests/test_review_contract.py`

- [ ] **Step 1: Write the failing contract tests**

```python
import unittest
from contracts.review_result import build_degraded_report

class TestReviewContract(unittest.TestCase):
    def test_degraded_report_has_stable_required_fields(self):
        report = build_degraded_report(session_id="s1", run_id="r1", reason="timeout")
        self.assertEqual(report["schema_version"], "review_result.v1")
        self.assertEqual(report["status"], "degraded_complete")
        self.assertIn("dimension_scores", report)
        self.assertIn("issues", report)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m unittest -q backend/tests/test_review_contract.py`  
Expected: FAIL with `ModuleNotFoundError` or missing fields.

- [ ] **Step 3: Implement the contract module and schema alignment**

```python
SCHEMA_VERSION = "review_result.v1"

def build_degraded_report(session_id: str, run_id: str, reason: str) -> dict:
    return {
        "schema_version": SCHEMA_VERSION,
        "session_id": session_id,
        "run_id": run_id,
        "status": "degraded_complete",
        "degraded_reason": reason,
        "total_score": 0.0,
        "recommendation": "MODIFY",
        "dimension_scores": [],
        "issues": [],
        "summary": "Degraded completion due to upstream failure.",
    }
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m unittest -q backend/tests/test_review_contract.py`  
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/contracts/review_result.py backend/api/schemas.py backend/tests/test_review_contract.py
git commit -m "feat: add canonical review result contract v1"
```

### Task 2: Versioned SSE Envelope

**Files:**
- Modify: `backend/services/sse_service.py`
- Test: `backend/tests/test_sse_envelope.py`

- [ ] **Step 1: Write failing SSE envelope tests**

```python
import unittest
from services.sse_service import SSEService

class TestSSEEnvelope(unittest.IsolatedAsyncioTestCase):
    async def test_dimension_start_event_has_envelope(self):
        sse = SSEService(session_id="s1", run_id="r1")
        await sse.push_dimension_start("Completeness")
        event = await sse._queue.get()
        self.assertEqual(event["schema_version"], "sse_event.v1")
        self.assertEqual(event["run_id"], "r1")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m unittest -q backend/tests/test_sse_envelope.py`  
Expected: FAIL because `run_id/schema_version` keys are missing.

- [ ] **Step 3: Implement envelope wrapper**

```python
def _wrap(self, event_type: str, payload: dict) -> dict:
    return {
        "event_type": event_type,
        "schema_version": "sse_event.v1",
        "session_id": self.session_id,
        "run_id": self.run_id,
        "ts": datetime.utcnow().isoformat() + "Z",
        "payload": payload,
    }
```

- [ ] **Step 4: Run tests**

Run: `python -m unittest -q backend/tests/test_sse_envelope.py`  
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/services/sse_service.py backend/tests/test_sse_envelope.py
git commit -m "feat: add versioned SSE envelope with run metadata"
```

### Task 3: Result Pipeline (`parse -> normalize -> validate -> repair`)

**Files:**
- Create: `backend/services/result_pipeline.py`
- Modify: `backend/services/review_service.py`
- Test: `backend/tests/test_result_pipeline.py`

- [ ] **Step 1: Write failing result pipeline tests**

```python
import unittest
from services.result_pipeline import ResultPipeline

class TestResultPipeline(unittest.TestCase):
    def test_invalid_json_returns_degraded_when_repair_exhausted(self):
        pipeline = ResultPipeline(max_repair_attempts=2)
        parsed = pipeline.process(raw_text="{bad-json", session_id="s1", run_id="r1")
        self.assertEqual(parsed["status"], "degraded_complete")
```

- [ ] **Step 2: Run test to verify failure**

Run: `python -m unittest -q backend/tests/test_result_pipeline.py`  
Expected: FAIL with import/attribute errors.

- [ ] **Step 3: Implement minimal pipeline**

```python
class ResultPipeline:
    def process(self, raw_text: str, session_id: str, run_id: str) -> dict:
        try:
            payload = self._strict_parse(raw_text)
            normalized = self._normalize(payload)
            self._validate(normalized)
            return normalized
        except Exception:
            return build_degraded_report(session_id=session_id, run_id=run_id, reason="parse_or_validate_failed")
```

- [ ] **Step 4: Integrate into review service**

Run in `review_service.py`: call `ResultPipeline.process(...)` for each model result before report aggregation.

- [ ] **Step 5: Run tests**

Run: `python -m unittest -q backend/tests/test_result_pipeline.py`  
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add backend/services/result_pipeline.py backend/services/review_service.py backend/tests/test_result_pipeline.py
git commit -m "feat: add strict result pipeline with degraded fallback"
```

### Task 4: Secondary Verifier for Drift Control

**Files:**
- Create: `backend/services/verification_service.py`
- Modify: `backend/services/review_service.py`
- Test: `backend/tests/test_verification_service.py`

- [ ] **Step 1: Write failing verifier tests**

```python
import unittest
from services.verification_service import VerificationService

class TestVerificationService(unittest.TestCase):
    def test_flags_missing_evidence_on_high_issue(self):
        verifier = VerificationService()
        report = {"issues": [{"severity": "HIGH", "title": "Missing AC"}]}
        out = verifier.verify(report)
        self.assertTrue(out["has_blocking_issues"])
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m unittest -q backend/tests/test_verification_service.py`  
Expected: FAIL.

- [ ] **Step 3: Implement verifier checks**

```python
class VerificationService:
    KEY_DIMENSIONS = {"completeness", "feasibility", "risk"}

    def verify(self, report: dict) -> dict:
        findings = []
        for issue in report.get("issues", []):
            if issue.get("severity") == "HIGH" and not issue.get("location"):
                findings.append("HIGH issue missing evidence location")
        return {"has_blocking_issues": bool(findings), "findings": findings}
```

- [ ] **Step 4: Add review service integration**

Apply verifier before final emit; if blocking, downgrade recommendation or set degraded reason.

- [ ] **Step 5: Run tests**

Run: `python -m unittest -q backend/tests/test_verification_service.py`  
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add backend/services/verification_service.py backend/services/review_service.py backend/tests/test_verification_service.py
git commit -m "feat: add secondary verification for consistency and evidence"
```

### Task 5: Run Registry and Idempotent Start

**Files:**
- Create: `backend/services/run_registry.py`
- Modify: `backend/api/routes.py`
- Modify: `backend/api/schemas.py`
- Test: `backend/tests/test_run_registry.py`
- Test: `backend/tests/test_routes_idempotency.py`

- [ ] **Step 1: Write failing run registry tests**

```python
import unittest
from services.run_registry import RunRegistry

class TestRunRegistry(unittest.TestCase):
    def test_same_session_and_params_reuses_run(self):
        reg = RunRegistry()
        run1 = reg.get_or_create("s1", {"preset": "normal"})
        run2 = reg.get_or_create("s1", {"preset": "normal"})
        self.assertEqual(run1.run_id, run2.run_id)
```

- [ ] **Step 2: Run tests and capture expected failure**

Run: `python -m unittest -q backend/tests/test_run_registry.py`  
Expected: FAIL.

- [ ] **Step 3: Implement run registry**

```python
@dataclass
class RunHandle:
    run_id: str
    state: str

class RunRegistry:
    def get_or_create(self, session_id: str, params: dict) -> RunHandle:
        key = (session_id, json.dumps(params, sort_keys=True))
        ...
```

- [ ] **Step 4: Wire registry into `/review/start`**

Ensure `StartReviewResponse` includes `run_id` and idempotency behavior.

- [ ] **Step 5: Add route-level idempotency test**

Run: `python -m unittest -q backend/tests/test_routes_idempotency.py`  
Expected: PASS with repeated start returning same `run_id`.

- [ ] **Step 6: Commit**

```bash
git add backend/services/run_registry.py backend/api/routes.py backend/api/schemas.py backend/tests/test_run_registry.py backend/tests/test_routes_idempotency.py
git commit -m "feat: add run registry and idempotent review start"
```

### Task 6: Artifact Persistence and Traceability

**Files:**
- Create: `backend/services/run_artifact_store.py`
- Modify: `backend/services/review_service.py`
- Test: `backend/tests/test_review_service_reliability.py`

- [ ] **Step 1: Write failing artifact persistence test**

```python
import unittest
from pathlib import Path
from services.run_artifact_store import RunArtifactStore

class TestArtifactStore(unittest.TestCase):
    def test_writes_report_json_for_run(self):
        store = RunArtifactStore(base_dir=Path("backend/tmp_runs"))
        p = store.write_report(run_id="r1", report={"status": "completed"})
        self.assertTrue(p.exists())
```

- [ ] **Step 2: Run tests**

Run: `python -m unittest -q backend/tests/test_review_service_reliability.py`  
Expected: FAIL.

- [ ] **Step 3: Implement artifact store and integrate in review service**

```python
class RunArtifactStore:
    def write_report(self, run_id: str, report: dict) -> Path:
        run_dir = self.base_dir / run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        out = run_dir / "final_report.json"
        out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        return out
```

- [ ] **Step 4: Run tests**

Run: `python -m unittest -q backend/tests/test_review_service_reliability.py`  
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/services/run_artifact_store.py backend/services/review_service.py backend/tests/test_review_service_reliability.py
git commit -m "feat: persist run artifacts for reliability traceability"
```

### Task 7: Reliability Benchmark and CI Gate

**Files:**
- Create: `backend/tests/reliability/test_reliability_metrics.py`
- Create: `.github/workflows/reliability-gate.yml`
- Modify: `README.md`

- [ ] **Step 1: Write failing benchmark test scaffold**

```python
def test_recommendation_consistency_threshold():
    metrics = {"recommendation_consistency": 0.96, "score_stddev": 0.30, "high_issue_overlap": 0.90}
    assert metrics["recommendation_consistency"] >= 0.95
    assert metrics["score_stddev"] <= 0.35
    assert metrics["high_issue_overlap"] >= 0.85
```

- [ ] **Step 2: Run benchmark test**

Run: `python -m unittest discover -q backend/tests/reliability`  
Expected: PASS locally with fixture metrics.

- [ ] **Step 3: Add reliability CI workflow**

```yaml
name: reliability-gate
on: [push, pull_request]
jobs:
  reliability:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: pip install -r backend/requirements.txt
      - run: python -m unittest discover -q backend/tests
```

- [ ] **Step 4: Document reliability checks in README**

Add a section with commands and metric thresholds.

- [ ] **Step 5: Commit**

```bash
git add backend/tests/reliability/test_reliability_metrics.py .github/workflows/reliability-gate.yml README.md
git commit -m "chore: add reliability benchmark and CI gate"
```

### Task 8: Final Verification Pass

**Files:**
- Modify: none (verification-only)
- Test: all affected tests

- [ ] **Step 1: Run backend reliability tests**

Run: `python -m unittest discover -q backend/tests`  
Expected: PASS.

- [ ] **Step 2: Run existing repo tests**

Run: `python -m unittest discover -q`  
Expected: Existing known layout constraints may still fail unless frontend/import-related files are present.

- [ ] **Step 3: Manual API smoke check**

Run server:

```bash
cd backend
uvicorn main:app --reload
```

Check endpoints:

1. `POST /api/review/upload`
2. `POST /api/review/start` (expect `run_id`)
3. `GET /api/review/stream/{session_id}` (expect versioned envelope)
4. `GET /api/review/report/{session_id}` (expect `schema_version/status`)

- [ ] **Step 4: Commit final verification notes**

```bash
git add .
git commit -m "test: verify reliability pipeline end-to-end"
```

---

## Execution Notes

1. Follow DRY/YAGNI: do not introduce extra abstraction until tests require it.
2. Keep backward compatibility in API payloads for at least one migration window.
3. Prefer small commits exactly as listed to simplify rollback.
4. If drift thresholds fail in Task 7, stop and adjust verifier logic before continuing.
