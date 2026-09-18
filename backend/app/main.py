from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.admin.views import setup_admin
from app.api.routers import health, tracks
from app.core.config import get_settings


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="Spletni API",
        version="0.1.0",
        description="Art Spletni audio guide platform API",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.public_base_url, "http://localhost:5174"],
        allow_methods=["GET"],
        allow_headers=["*"],
    )

    app.include_router(health.router)
    app.include_router(tracks.router)

    setup_admin(app)

    return app


app = create_app()
