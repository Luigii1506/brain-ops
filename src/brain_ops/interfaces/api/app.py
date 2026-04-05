"""FastAPI application factory for brain-ops API."""

from __future__ import annotations

from fastapi import FastAPI

from .routes_entities import router as entities_router
from .routes_projects import router as projects_router
from .routes_sources import router as sources_router
from .routes_personal import router as personal_router


def create_api_app() -> FastAPI:
    app = FastAPI(
        title="brain-ops API",
        description="REST API for the brain-ops personal intelligence station.",
        version="0.1.0",
    )
    app.include_router(entities_router, prefix="/entities", tags=["knowledge"])
    app.include_router(projects_router, prefix="/projects", tags=["projects"])
    app.include_router(sources_router, prefix="/sources", tags=["monitoring"])
    app.include_router(personal_router, prefix="/personal", tags=["personal"])
    return app
