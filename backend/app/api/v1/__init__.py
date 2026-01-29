"""API v1 модули."""

from fastapi import APIRouter

from app.api.v1 import auth, health, vacancy

router = APIRouter(prefix="/v1")

router.include_router(health.router, tags=["Health"])
router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
router.include_router(vacancy.router, prefix="/vacancy", tags=["Vacancy"])
