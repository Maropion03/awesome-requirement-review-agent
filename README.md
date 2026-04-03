# Awesome Requirement Review Agent 

**English** | [中文](README_CN.md)

An AI-powered PRD (Product Requirements Document) review system built on multi-agent collaboration. Upload a PRD, and AI agents automatically review it across 6 dimensions with real-time streaming progress and structured reports.

## Live Demo

👉 **[Try it now](https://awesome-requirement-review-agent-production.up.railway.app/single-page-shell.html)** — No setup required, just upload your PRD.

## Features

- **6-Dimension Review** — Completeness, Reasonableness, User Value, Feasibility, Risk, Priority Consistency
- **Multi-Agent Collaboration** — Dev / Design / Test agents review in parallel, coordinated by an Orchestrator
- **3 Review Presets** — Standard / P0 Critical / Innovation, with auto-adjusted scoring weights
- **Real-time Streaming** — SSE-based live progress updates as each dimension is reviewed
- **AI Chat** — Post-review interactive Q&A to dive deeper into specific issues
- **Report Export** — PDF and Markdown export
- **Document Parsing** — Supports .docx and .md uploads
- **Rate Limiting** — IP-based throttling via slowapi to prevent abuse

## Architecture

```
┌─────────────────────────────────────────────────┐
│              Frontend (Single Page HTML)          │
│              Tailwind CSS + Chart.js             │
├─────────────────────────────────────────────────┤
│              FastAPI Backend                      │
│  ├── API Routes (upload/review/chat/export)      │
│  ├── SSE Service (real-time streaming)           │
│  ├── Review Service (review workflow)            │
│  └── Chat Service (post-review Q&A)             │
├─────────────────────────────────────────────────┤
│              Multi-Agent Layer (CrewAI)           │
│  ├── Orchestrator                                │
│  ├── Dimension Reviewers × 6                     │
│  └── Reporter                                    │
├─────────────────────────────────────────────────┤
│              MiniMax LLM API                     │
└─────────────────────────────────────────────────┘
```

## Quick Start

### Local Development

```bash
git clone git@github.com:Maropion03/awesome-requirement-review-agent.git
cd awesome-requirement-review-agent/backend
cp .env.example .env   # then fill in your MiniMax API credentials
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

### Docker

```bash
docker build -t prd-reviewer .
docker run -p 8000:8000 \
  -e MINIMAX_API_KEY=your_key \
  -e MINIMAX_API_BASE=https://api.minimax.chat/v1 \
  -e MINIMAX_CHAT_MODEL=MiniMax-M2.7 \
  prd-reviewer
```

## Project Structure

```
├── Dockerfile              # Multi-stage build (frontend compile + backend runtime)
├── backend/
│   ├── main.py             # FastAPI entry + SPA static file serving
│   ├── api/
│   │   ├── routes.py       # API routes (upload/review/chat/share)
│   │   └── schemas.py      # Pydantic data models
│   ├── agents/
│   │   ├── orchestrator.py # Review orchestrator
│   │   ├── reviewers.py    # 6-dimension review agents
│   │   └── reporter.py     # Report generation agent
│   ├── services/
│   │   ├── review_service.py  # Review workflow
│   │   ├── sse_service.py     # SSE streaming
│   │   └── chat_service.py    # Post-review chat
│   ├── tools/
│   │   ├── parser.py       # PRD document parser (.md / .docx)
│   │   └── validator.py    # Input validation
│   ├── config/
│   │   └── prompts.py      # Prompt templates + preset weight configs
│   └── utils/              # MiniMax client + report utilities
├── frontend/
│   └── public/
│       └── single-page-shell.html  # Single-page frontend (Tailwind + Chart.js)
└── tests/                  # Unit tests
```

## API

| Method | Path | Description | Rate Limit |
|--------|------|-------------|-----------|
| POST | `/api/review/upload` | Upload PRD document | 10/min |
| POST | `/api/review/start` | Start review | 5/min |
| GET | `/api/review/stream/{session_id}` | SSE review progress | — |
| GET | `/api/review/status/{session_id}` | Query review status | — |
| GET | `/api/review/report/{session_id}` | Get review report | — |
| POST | `/api/review/chat` | Post-review chat | 20/min |
| GET | `/api/review/export/pdf/{session_id}` | Export PDF report | — |
| POST | `/api/review/config` | Configure review agents | — |
| GET | `/health` | Health check | — |

## Review Dimensions & Weights

### Standard Project

| Dimension | Weight | Focus |
|-----------|--------|-------|
| Completeness | 20% | Feature descriptions, acceptance criteria, edge cases |
| Reasonableness | 20% | Logical consistency, scenario coverage |
| User Value | 20% | Pain point resolution, ROI |
| Feasibility | 20% | Architecture soundness, dependency availability |
| Risk | 10% | Technical risk, timeline risk |
| Priority Consistency | 10% | Priority-resource alignment |

### P0 Critical Project

Completeness 35% + Feasibility 35% + Risk 20% + Others 10%

### Innovation Project

User Value 40% + Completeness 30% + Others 30%

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | HTML + Tailwind CSS + Chart.js |
| Backend | FastAPI + SSE (sse-starlette) |
| AI Framework | CrewAI (Multi-Agent) |
| LLM | MiniMax-M2.7 |
| Doc Parsing | python-docx + Markdown |
| Report Export | ReportLab (PDF) |
| Rate Limiting | slowapi |
| Deployment | Docker + Railway |

## License

MIT
