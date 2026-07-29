# Public route metadata

The app is a client-side tool with one public entry route. `frontend/index.html` supplies a Chinese title, description, viewport, language, and theme color. Vercel serves the built `index.html` as the SPA fallback after `/api/*` rewrites.

Report and assistant views are hash routes containing user-generated in-memory content. They are intentionally not separate indexable URLs and contain no server-rendered PRD data.
