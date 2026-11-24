from fastapi import FastAPI

from app.core.config import get_settings
from app.core.exceptions import register_exception_handlers

from app.api.auth import router as auth_router
from app.api.workspace import router as workspace_router

settings = get_settings()
app = FastAPI(title="DocMind API", version="0.1.0")

register_exception_handlers(app)
app.include_router(auth_router, prefix="/api/v1")
app.include_router(workspaces_router, prefix="/api/v1")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "env": settings.app_env}
