from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api.routes import router as api_router
from app.core.config import settings

app = FastAPI(title=settings.app_name)
app.include_router(api_router, prefix="/api")

if settings.static_dir_exists:
    app.mount("/", StaticFiles(directory=str(settings.static_path), html=True), name="static")
