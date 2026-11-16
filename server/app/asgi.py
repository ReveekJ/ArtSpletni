import logging

import click
from advanced_alchemy.extensions.litestar import SQLAlchemyPlugin
from litestar import Litestar
from litestar.config.app import AppConfig
from litestar.config.cors import CORSConfig
from litestar.di import Provide
from litestar.logging import LoggingConfig
from litestar.middleware import DefineMiddleware
from litestar.openapi import OpenAPIConfig
from litestar.openapi.plugins import ScalarRenderPlugin
from litestar.plugins import CLIPluginProtocol, InitPluginProtocol
from litestar.stores.registry import StoreRegistry
from litestar.types import ControllerRouterHandler

from app.config import alchemy_config, build_stores, provide_email_service, session_config
from app.domain.achievements.cli import seed_achievements_command
from app.domain.achievements.controllers import AdminAchievementController, MyAchievementsController
from app.domain.analytics.controllers import AdminAnalyticsController, PlaybackController
from app.domain.auth.cli import seed_demo_users_command
from app.domain.auth.controllers import AuthController
from app.domain.auth.middleware import SessionUserMiddleware
from app.domain.i18n.controllers import AdminTranslationController, LanguagesController
from app.domain.i18n.deps import provide_language, provide_translation_service
from app.domain.media.controllers import AdminMediaController
from app.domain.media.deps import provide_media_service
from app.domain.offers.controllers import MyOffersController
from app.domain.partners.controllers import (
    AdminOfferController,
    AdminPartnerController,
    PartnerCabinetController,
)
from app.domain.points.controllers import (
    AdminPointController,
    AdminTagController,
    CollectionController,
    PointController,
)
from app.domain.routes.controllers import AdminRouteController
from app.domain.runs.controllers import RouteController, RunController
from app.domain.scans.controllers import ScanController
from app.domain.submissions.controllers import AdminSubmissionController, MySubmissionsController
from app.domain.system.controllers import HealthController
from app.domain.users.cli import create_admin_command
from app.lib.exceptions import ApplicationError, application_error_handler
from app.lib.http import http_client_lifespan, provide_http_client
from app.lib.settings import get_settings

ROUTE_HANDLERS: list[ControllerRouterHandler] = [
    HealthController,
    AuthController,
    LanguagesController,
    AdminTranslationController,
    AdminMediaController,
    AdminPointController,
    AdminTagController,
    AdminRouteController,
    PointController,
    CollectionController,
    ScanController,
    RouteController,
    RunController,
    MyOffersController,
    AdminPartnerController,
    AdminOfferController,
    PartnerCabinetController,
    AdminAchievementController,
    MyAchievementsController,
    MySubmissionsController,
    AdminSubmissionController,
    PlaybackController,
    AdminAnalyticsController,
]


class ApplicationCore(InitPluginProtocol, CLIPluginProtocol):
    def on_app_init(self, app_config: AppConfig) -> AppConfig:
        settings = get_settings()
        app_config.route_handlers.extend(ROUTE_HANDLERS)
        app_config.exception_handlers[ApplicationError] = application_error_handler
        app_config.stores = StoreRegistry(stores=dict(build_stores()))
        app_config.middleware.extend(
            [
                session_config().middleware,
                DefineMiddleware(SessionUserMiddleware, exclude=["/schema"]),
            ]
        )
        app_config.dependencies.update(
            {
                "http_client": Provide(provide_http_client, sync_to_thread=False),
                "language": Provide(provide_language),
                "email_service": Provide(provide_email_service),
                "media_service": Provide(provide_media_service),
                "translation_service": Provide(provide_translation_service),
            }
        )
        app_config.lifespan.append(http_client_lifespan)
        if settings.cors_allowed_origins:
            app_config.cors_config = CORSConfig(
                allow_origins=settings.cors_allowed_origins, allow_credentials=True
            )
        app_config.openapi_config = OpenAPIConfig(
            title="Spletni API",
            version="1.0.0",
            path="/schema",
            render_plugins=[ScalarRenderPlugin()],
        )
        app_config.logging_config = LoggingConfig(
            root={"level": logging.getLevelName(logging.INFO), "handlers": ["queue_listener"]},
            log_exceptions="always",
        )
        return app_config

    def on_cli_init(self, cli: click.Group) -> None:
        cli.add_command(create_admin_command)
        cli.add_command(seed_achievements_command)
        cli.add_command(seed_demo_users_command)


def create_app() -> Litestar:
    return Litestar(
        plugins=[
            SQLAlchemyPlugin(config=alchemy_config()),
            ApplicationCore(),
        ],
    )
