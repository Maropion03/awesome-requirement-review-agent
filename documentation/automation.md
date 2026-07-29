# LLM workflow behavior

The review is request-driven automation. It has no schedule, queue, background worker, or hidden trigger.

## Trigger and termination

- Trigger: authenticated-by-key model call initiated by the user pressing “开始六维评审”.
- Progress: one NDJSON response on the same HTTP request.
- Terminal state: `complete` or `error`; `complete` may carry `degraded_complete` report status.
- Cancellation: browser `AbortController` when the component closes or a run is reset.

## Retries and bounded work

- Network timeout: one retry.
- Invalid structured reviewer output: one repair request.
- Review dimensions: six concurrent tasks, no recursive agents or tools.
- Reporter: deterministic local code, no additional model call.

The run ID is a stable hash of the review date and document prefix for traceability; it is not a server idempotency store. Re-clicking starts a new billable provider run, and the UI disables the button while a run is active.

## Degraded mode

A failed dimension is assigned score `0`, records a sanitized reason, and is listed in `degraded_dimensions`. This makes the partial nature of the result visible and prevents a missing event from masquerading as a complete review.
