# PDF Diagram to Mermaid Design

## Goal

Avoid Vercel's false-positive rejection of raw PDF multipart bodies while preserving text and important flowchart semantics for PRD review.

## Flow

1. Load `pdf.js` only after the user starts a PDF review.
2. Extract and clean text page by page in the browser.
3. Count image paint operations and render up to four image-heavy candidate pages as compressed JPEGs.
4. Send extracted text and candidate JPEGs to Vercel; never send the original PDF bytes.
5. Make one multimodal call using the configured API format and optional separate vision model.
6. Require structured nodes, indexed edges, page number, confidence, and unresolved labels.
7. Generate Mermaid deterministically in Python and append it to the text context shared by all six reviewers.
8. Return diagram status and Mermaid source in the report. If vision fails or the model lacks image support, continue a text-only review with a visible stream warning.

## Limits

- Maximum four candidate pages.
- JPEG or PNG only, maximum 700KB per candidate page.
- Mermaid is derived evidence and must be checked against the original page.
- A blank vision model reuses the review model. For the official Zhipu endpoint, a GLM-5.3 review configuration defaults diagram recognition to `glm-4.6v-flash` because GLM-5.3 only supports text.
- Ordinary UI screenshots are excluded by the vision prompt.
- Scanned PDFs without an extractable text layer remain unsupported unless OCR is added separately.

## Verification

- Browser contract confirms raw PDF bytes are absent from the multipart request.
- Protocol tests cover image blocks for OpenAI Chat Completions, OpenAI Responses, and Anthropic Messages.
- Pipeline tests confirm one vision call and Mermaid reuse across six reviews.
- The previously blocked PDF must reach the production FastAPI endpoint without `x-vercel-mitigated: deny`.
