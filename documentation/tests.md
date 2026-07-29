# Verification

## Backend

```bash
uv sync --dev
uv run pytest -q tests
```

Coverage includes provider request shapes, fixed hosts, credential validation, sanitized upstream errors, in-memory parsing, concurrent reviewers, degraded completion, stable issue identity, and the one-request streaming API.

## Frontend

```bash
cd frontend
npm test
npm run build
npm audit
```

Contracts cover the Vue root entry, BYOK payloads, no session/EventSource flow, NDJSON consumption, 0–100 report mapping, issue state/export, and UI copy.

## Local deterministic skill

```bash
uv run pytest -q skill-for-agent/tests --import-mode=importlib
```

## Dependency audit

```bash
npm audit --prefix frontend
uvx --from pip-audit pip-audit --path .venv/lib/python3.12/site-packages -s osv
```

## Vercel

```bash
vercel build
vercel --prod
curl -fsS https://<deployment>/api/health
curl -fsS https://<deployment>/api/providers
```

A model-backed production review requires a user-owned Key and is not part of unauthenticated CI.

`.github/workflows/ci.yml` runs backend, frontend, build, and npm audit checks on pushes and pull requests. A manual dispatch can receive `smoke_url` and verify the public SPA, health response, six-provider catalog, and absence of provider base URLs from an external GitHub-hosted runner.
