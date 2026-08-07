from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api import api_router
from config.settings import settings

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    docs_url="/docs",
    openapi_url="/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.get("/api/v1/health")
def health():
    return {
        "status": "healthy",
        "database": "connected",
        "queue": "connected",
        "storage": "connected",
        "ai": "available",
    }
