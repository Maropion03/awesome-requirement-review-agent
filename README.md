# Awesome Requirement Review Agent

[![CI](https://github.com/Maropion03/awesome-requirement-review-agent/actions/workflows/ci.yml/badge.svg)](https://github.com/Maropion03/awesome-requirement-review-agent/actions/workflows/ci.yml)
[![Live on Vercel](https://img.shields.io/badge/live-Vercel-000000?logo=vercel)](https://awesome-requirement-review-agent.vercel.app)
[![Python 3.12](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI 0.140.7](https://img.shields.io/badge/FastAPI-0.140.7-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Vue 3](https://img.shields.io/badge/Vue-3-42B883?logo=vuedotjs&logoColor=white)](https://vuejs.org/)
[![BYOK](https://img.shields.io/badge/AI-BYOK-ef6c00)](#api-key-handling)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)

An open-source PRD review workbench for product teams. Bring your own model API key, upload a Markdown or DOCX PRD, and receive a six-dimension review with evidence, scores, and actionable revisions.

> The app is stateless. It has no built-in MiniMax key, no account system, and no server-side document or report storage.

**[Open the live workbench](https://awesome-requirement-review-agent.vercel.app)** · [中文说明](./README_CN.md)

## Highlights

- Six concurrent review dimensions: completeness, rationality, user value, technical feasibility, implementation risk, and priority alignment.
- Evidence-linked issues with severity, actionable revisions, local handling status, and Markdown export.
- Report-aware follow-up assistant that can explain conclusions, locate source text, and draft PRD-ready changes.
- Dedicated browser-persisted BYOK settings for six mainstream model providers.
- Stateless Vercel architecture: no built-in model key, account system, server session, or document database.

## What changed in v2

- Migrated from the retired Railway deployment to Vercel.
- Replaced the embedded/server-owned MiniMax setup with BYOK.
- Supports MiniMax, OpenAI, Anthropic, DeepSeek, Gemini, and OpenRouter.
- Adds a dedicated API settings page and persists provider, model, preset, and key in this browser.
- Uses fixed official provider hosts; users can choose a model but cannot supply an arbitrary base URL.
- Replaced process-local uploads, background jobs, sessions, SSE reconnects, and shares with one streaming request.
- Runs all six reviewers concurrently and produces a deterministic aggregate report.
- Validates model JSON, retries one repair, and visibly degrades a failed dimension instead of hanging.
- Removed CrewAI/LangChain and the duplicate static frontend.

## API key handling

The provider, model, preset, and key are stored as plaintext in this browser's `localStorage` so the configuration survives refreshes and browser restarts. Each validation, review, or chat request sends the key through the Vercel Function to the selected provider. The app does not write keys to cookies, a server-side database, files, analytics, or logs. Use **Clear local configuration** on shared devices or clear the site's browser data.

Browser storage is a convenience/security tradeoff: scripts running on this origin can read the stored key. The key also transits the serverless function, so the Vercel deployment operator must still be trusted. Self-host if the PRD or key cannot pass through a third-party deployment.

## Supported providers

| Provider | Protocol | Default model |
| --- | --- | --- |
| MiniMax | OpenAI-compatible | `MiniMax-M2.7` |
| OpenAI | OpenAI Chat Completions | `gpt-5.2` |
| Anthropic | Messages API | `claude-sonnet-5` |
| DeepSeek | OpenAI-compatible | `deepseek-v4-flash` |
| Google Gemini | OpenAI-compatible | `gemini-3.6-flash` |
| OpenRouter | OpenAI-compatible | `~openai/gpt-latest` |

Model catalogs change. The model field is editable so users can choose another model available to their account.

## Local development

Requirements: Python 3.12+, Node.js 22+, and `uv` (recommended).

```bash
uv sync --dev
uv run uvicorn backend.app:app --reload --port 8005
```

In another terminal:

```bash
cd frontend
npm ci --include=dev
npm run dev
```

Open `http://localhost:5173`. No `.env` or server API key is required.

## Test and build

```bash
uv sync --dev
uv run pytest -q tests
cd frontend && npm test && npm run build && npm audit
uv run pytest -q skill-for-agent/tests --import-mode=importlib
vercel build
```

## Deploy to Vercel

```bash
vercel
vercel --prod
```

The repository includes [`vercel.json`](./vercel.json). Production needs no secret environment variables. Vercel builds the Vue app into `frontend/dist` and deploys `api/index.py` as the FastAPI function.

## Runtime API

| Method | Endpoint | Purpose |
| --- | --- | --- |
| GET | `/api/health` | Stateless runtime health |
| GET | `/api/providers` | Public provider/model presets; never returns keys or base URLs |
| POST | `/api/providers/validate` | Minimal model connection test |
| POST | `/api/review/run` | Multipart document + BYOK config; returns NDJSON progress and report |
| POST | `/api/review/chat` | Stateless report follow-up |

Uploads are capped at 3.5MB because Vercel Function request bodies have a 4.5MB platform limit. Extracted text is capped at 80,000 characters to prevent accidental oversized contexts and cost. A complete review makes six concurrent model calls; validation, JSON repair, and chat can add calls.

## Repository layout

```text
api/index.py                 Vercel Python entrypoint
backend/app.py               FastAPI routes
backend/core/                provider adapters, parser, schemas, review pipeline
frontend/src/                maintained Vue application
tests/                       backend behavior/security tests
frontend/tests/              frontend contract tests
skill-for-agent/             separate deterministic local review skill
documentation/               architecture, flows, permissions, variables, tests
```

## License

[MIT](./LICENSE)
