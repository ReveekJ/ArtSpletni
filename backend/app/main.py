from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

from app.admin import setup_admin
from app.api.routers import (
    admin,
    admin_analytics,
    admin_localizations,
    admin_routes,
    admin_submissions,
    admin_tracks,
    analytics,
    auth,
    checkpoints,
    health,
    nfc,
    routes,
    submissions,
    tracks,
)
from app.core.config import get_settings


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="Spletni API",
        version="0.1.0",
        description="Art Spletni audio guide platform API",
    )

    app.add_middleware(
        SessionMiddleware,
        secret_key=settings.session_secret,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.public_base_url, "http://localhost:5173"],
        allow_methods=["GET", "POST", "DELETE", "PATCH", "PUT"],
        allow_headers=["*"],
    )

    app.include_router(health.router)
    app.include_router(auth.router)
    app.include_router(nfc.router)
    app.include_router(tracks.router)
    app.include_router(checkpoints.router)
    app.include_router(routes.router)
    app.include_router(submissions.router)
    app.include_router(analytics.router)
    app.include_router(admin.router)
    app.include_router(admin_analytics.router)
    app.include_router(admin_submissions.router)
    app.include_router(admin_routes.router)
    app.include_router(admin_routes.checkpoint_router)
    app.include_router(admin_tracks.router)
    app.include_router(admin_localizations.router)

    setup_admin(app)

    return app


app = create_app()
