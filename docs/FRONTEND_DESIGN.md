# Frontend design

The maintained UI is the Vue application in `frontend/src`; there is no redirecting static shell.

## Core interaction

1. Select a Markdown/DOCX document (3.5MB maximum).
2. Select a supported provider, enter an in-memory API Key, edit the model if needed, and optionally test the connection.
3. Start one cancellable streaming review request and observe six dimension states.
4. Inspect the 0–100 report, evidence, and local issue state; export suggestions as Markdown.
5. Ask stateless follow-up questions using the current report and Key.

## Visual direction

The workbench uses an editorial instrument-panel language: warm paper grid, black controls, one safety-orange accent, compact monospaced metadata, and a clear three-step flow. The API configuration is a single horizontal control surface rather than nested cards. Responsive layouts collapse provider and configuration grids without changing behavior.

No WebGL or Three.js layer is used: this is a key-entry and document-analysis tool, so animation and GPU cost would not improve task comprehension or trust.

See [`../documentation/flows.md`](../documentation/flows.md) and [`../documentation/permissions.md`](../documentation/permissions.md) for runtime behavior.
