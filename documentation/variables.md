# Runtime variables

## Production

No environment variable is required. In particular, do not configure `MINIMAX_API_KEY`, `OPENAI_API_KEY`, or another model secret on the Vercel project; keys belong to users.

| Variable | Scope | Default | Purpose |
| --- | --- | --- | --- |
| `LOCAL_DEV_ORIGINS` | FastAPI, optional | `http://localhost:5173,http://127.0.0.1:5173` | Comma-separated local CORS origins |
| `VITE_API_BASE_URL` | Vite build, optional | `/api` | Override API origin for an unusual local environment |

## Vercel configuration

`vercel.json` sets:

- frontend build command and `frontend/dist` output;
- `api/index.py` as the Python Function;
- 300-second maximum function duration;
- API rewrite before SPA fallback.

No model Key belongs in Vercel Environment Variables.
