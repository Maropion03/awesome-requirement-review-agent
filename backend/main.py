import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from api.routes import router as api_router

BACKEND_ROOT = Path(__file__).resolve().parent
load_dotenv(BACKEND_ROOT / ".env")

DEFAULT_CORS_ORIGINS = {
    "http://localhost:3000",
    "http://localhost:5173",
    "http://localhost:5176",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:5176",
}


def _parse_cors_origins(raw_value: Optional[str]) -> list[str]:
    configured = []
    if raw_value:
        configured = [origin.strip() for origin in raw_value.split(",") if origin.strip()]

    # Always keep local dev origins available so the frontend can talk to the API
    # whether it runs on common local ports or the current Vite dev port.
    return list(dict.fromkeys(configured + sorted(DEFAULT_CORS_ORIGINS)))


CORS_ORIGINS = _parse_cors_origins(os.getenv("CORS_ORIGINS"))

# Rate limiter – keyed by client IP
limiter = Limiter(key_func=get_remote_address)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    os.makedirs("uploads", exist_ok=True)
    yield
    # Shutdown


app = FastAPI(
    title="PRD Reviewer API",
    description="PRD 评审系统后端 API",
    version="1.0.0",
    lifespan=lifespan,
)

# Attach rate limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api")


@app.get("/health")
async def health_check():
    return {"status": "ok"}


# --- SPA static file serving ---
STATIC_DIR = BACKEND_ROOT / "static"

if STATIC_DIR.is_dir():
    # Mount known static subdirectories that Vite may produce
    for subdir in ("assets",):
        sub_path = STATIC_DIR / subdir
        if sub_path.is_dir():
            app.mount(f"/{subdir}", StaticFiles(directory=sub_path), name=f"static-{subdir}")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        """Serve Vue SPA – return the actual file if it exists, otherwise index.html."""
        file_path = STATIC_DIR / full_path
        if full_path and file_path.is_file():
            return FileResponse(file_path)
        return FileResponse(STATIC_DIR / "index.html")
