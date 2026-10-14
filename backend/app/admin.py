from fastapi import FastAPI, Request
from sqladmin import Admin, ModelView
from sqladmin.authentication import AuthenticationBackend

from app.core.config import get_settings
from app.entities.audio_track import AudioTrack
from app.entities.checkpoint import Checkpoint
from app.entities.listen_session import ListenSession
from app.entities.route import Route
from app.entities.route_stop import RouteStop
from app.entities.route_stop_dependency import RouteStopDependency
from app.entities.track_access_grant import TrackAccessGrant
from app.entities.track_localization import TrackLocalization
from app.entities.user import User
from app.entities.user_progress import UserProgress


class AudioTrackAdmin(ModelView, model=AudioTrack):
    column_list = [
        AudioTrack.id,
        AudioTrack.slug,
        AudioTrack.title,
        AudioTrack.author,
        AudioTrack.moderation_status,
        AudioTrack.is_published,
    ]
    column_searchable_list = [AudioTrack.title, AudioTrack.slug, AudioTrack.author]
    column_default_sort = [("id", True)]
    form_columns = [
        AudioTrack.slug,
        AudioTrack.title,
        AudioTrack.description,
        AudioTrack.author,
        AudioTrack.audio_s3_key,
        AudioTrack.cover_s3_key,
        AudioTrack.latitude,
        AudioTrack.longitude,
        AudioTrack.location_name,
        AudioTrack.is_published,
        AudioTrack.moderation_status,
        AudioTrack.published_at,
    ]


class TrackLocalizationAdmin(ModelView, model=TrackLocalization):
    column_list = [
        TrackLocalization.id,
        TrackLocalization.track_id,
        TrackLocalization.language,
        TrackLocalization.title,
    ]
    column_default_sort = [("id", True)]


class TrackAccessGrantAdmin(ModelView, model=TrackAccessGrant):
    column_list = [
        TrackAccessGrant.id,
        TrackAccessGrant.track_id,
        TrackAccessGrant.expires_at,
        TrackAccessGrant.revoked_at,
    ]
    column_default_sort = [("id", True)]
    form_columns = [
        TrackAccessGrant.track_id,
        TrackAccessGrant.secret_hash,
        TrackAccessGrant.expires_at,
        TrackAccessGrant.revoked_at,
    ]


class ListenSessionAdmin(ModelView, model=ListenSession):
    column_list = [
        ListenSession.id,
        ListenSession.track_id,
        ListenSession.visitor_id,
        ListenSession.is_completed,
        ListenSession.created_at,
    ]
    column_default_sort = [("created_at", True)]
    column_searchable_list = [ListenSession.session_token, ListenSession.visitor_id]


class UserAdmin(ModelView, model=User):
    column_list = [
        User.id,
        User.email,
        User.display_name,
        User.is_admin,
    ]
    column_searchable_list = [User.email, User.display_name]
    column_default_sort = [("id", True)]


class UserProgressAdmin(ModelView, model=UserProgress):
    column_list = [
        UserProgress.id,
        UserProgress.user_id,
        UserProgress.route_stop_id,
        UserProgress.completed_at,
    ]
    column_default_sort = [("completed_at", True)]


class RouteAdmin(ModelView, model=Route):
    column_list = [
        Route.id,
        Route.slug,
        Route.title,
        Route.is_published,
    ]
    column_searchable_list = [Route.title, Route.slug]
    column_default_sort = [("id", True)]


class RouteStopAdmin(ModelView, model=RouteStop):
    column_list = [
        RouteStop.id,
        RouteStop.route_id,
        RouteStop.order_index,
        RouteStop.stop_type,
        RouteStop.completion_criteria,
    ]
    column_default_sort = [("id", True)]


class RouteStopDependencyAdmin(ModelView, model=RouteStopDependency):
    column_list = [
        RouteStopDependency.id,
        RouteStopDependency.route_stop_id,
        RouteStopDependency.depends_on_stop_id,
    ]
    column_default_sort = [("id", True)]


class CheckpointAdmin(ModelView, model=Checkpoint):
    column_list = [
        Checkpoint.id,
        Checkpoint.slug,
        Checkpoint.title,
        Checkpoint.content_type,
        Checkpoint.is_published,
    ]
    column_searchable_list = [Checkpoint.title, Checkpoint.slug]
    column_default_sort = [("id", True)]


class SessionAuthBackend(AuthenticationBackend):
    async def login(self, request: Request) -> bool:
        form = await request.form()
        username = form.get("username", "")
        password = form.get("password", "")
        settings = get_settings()
        if username == settings.admin_username and password == settings.admin_password:
            request.session.update({"admin": True})
            return True
        return False

    async def logout(self, request: Request) -> bool:
        request.session.clear()
        return True

    async def authenticate(self, request: Request) -> bool:
        return bool(request.session.get("admin"))


def setup_admin(app: FastAPI) -> None:
    from app.core.db import engine

    settings = get_settings()
    admin = Admin(
        app,
        engine,
        base_url="/sqladmin",
        title="Spletni Admin",
        authentication_backend=SessionAuthBackend(secret_key=settings.session_secret),
    )
    admin.add_view(AudioTrackAdmin)
    admin.add_view(TrackLocalizationAdmin)
    admin.add_view(TrackAccessGrantAdmin)
    admin.add_view(ListenSessionAdmin)
    admin.add_view(UserAdmin)
    admin.add_view(UserProgressAdmin)
    admin.add_view(RouteAdmin)
    admin.add_view(RouteStopAdmin)
    admin.add_view(RouteStopDependencyAdmin)
    admin.add_view(CheckpointAdmin)
