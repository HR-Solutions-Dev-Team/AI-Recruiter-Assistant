"""
FastAPI application entry point.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.v1 import router as api_v1_router
from app.core.config import settings
from app.core.redis import redis_client

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if settings.debug else logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    logger.info(f"Environment: {settings.environment}")

    await redis_client.connect()
    logger.info("Redis connected")

    yield

    # Shutdown
    await redis_client.disconnect()
    logger.info("Redis disconnected")
    logger.info("Application shutdown")


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
        "http://localhost:80",
        "http://localhost",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API routes
app.include_router(api_v1_router, prefix="/api")

# Legacy health endpoint (for backward compatibility)
@app.get("/api/health")
async def legacy_health():
    """Legacy health check (use /api/v1/health instead)."""
    redis_ok = await redis_client.ping()
    return {"status": "ok" if redis_ok else "degraded"}


# Static files (if exists)
if settings.static_dir_exists:
    app.mount("/", StaticFiles(directory=str(settings.static_path), html=True), name="static")
