# User and system flows

## Review

```mermaid
sequenceDiagram
    participant U as User
    participant B as Browser
    participant V as Vercel Function
    participant M as Model API

    U->>B: Select .md/.docx/.pdf and enter Key
    B->>V: POST /api/review/run (multipart)
    V->>V: Validate provider, key shape, type, size; parse in memory
    V-->>B: connected + six dimension_start events
    par Six concurrent dimensions
      V->>M: Review dimension with untrusted PRD
      M-->>V: JSON candidate
    end
    V->>V: Validate/repair; deterministically aggregate
    V-->>B: dimension_complete events + complete report
    B->>B: Track issue state and allow Markdown export
```

The terminal event is always either `complete` or `error`. A dimension error does not leave the browser waiting indefinitely.

## Connection test

1. User selects a provider, enters a Key, and sets a model.
2. Browser posts the three fields to `/api/providers/validate`.
3. Server makes a minimal completion request to the fixed provider host.
4. Browser displays a sanitized success or failure message.

The connection test consumes a small provider request and may incur a small charge.

## Report follow-up

1. The completed report remains in browser memory.
2. Browser posts Key, provider/model, report JSON, selected issue ID, and question to `/api/review/chat`.
3. The server sends report-only context to the model; the original PRD is not stored or reloaded.
4. The browser appends the answer to its in-memory chat.

## Export

Issue statuses and suggestions are rendered into Markdown in the browser and downloaded with a Blob URL. No server export job exists.
