import os
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from api.routes import router as api_router

load_dotenv()

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
