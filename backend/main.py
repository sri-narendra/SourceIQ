from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from api import api_router
from config.settings import settings
from database.session import Base, engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    # ponytail: create schema on boot so a fresh local DB works with a minimal .env;
    # swap for a real migration tool (alembic) when schema changes need versioning.
    try:
        with engine.begin() as conn:
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        Base.metadata.create_all(engine)
    except Exception:
        pass
    yield


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    docs_url="/docs",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url],
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1):\d+",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.get("/api/v1/health")
def health():
    db_ok = storage_ok = queue_ok = False
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        db_ok = True
    except Exception:
        db_ok = False

    if settings.s3_bucket_name and settings.aws_access_key_id:
        storage_ok = True
    if settings.sqs_queue_url:
        queue_ok = True
    has_ai = any(
        [
            (settings.ai_provider == "gemini" and settings.gemini_api_key),
            (settings.ai_provider == "groq" and settings.groq_api_key),
            (settings.ai_provider == "openai" and settings.openai_api_key),
            (settings.ai_provider == "mistral" and settings.mistral_api_key),
            (settings.ai_provider == "nvidia" and settings.nvidia_api_key),
            (settings.ai_provider == "openrouter" and settings.openrouter_api_key),
            (settings.ai_provider in ("vllm", "ollama") and settings.vllm_base_url),
        ]
    )

    status_val = "healthy" if db_ok and storage_ok and queue_ok else "degraded"

    return {
        "status": "degraded" if not db_ok else status_val,
        "database": "connected" if db_ok else "disconnected",
        "queue": "connected" if queue_ok else "not_configured",
        "storage": "connected" if storage_ok else "not_configured",
        "ai": "available" if has_ai else "unavailable",
    }
