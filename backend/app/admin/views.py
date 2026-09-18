import secrets

from markupsafe import Markup
from sqladmin import Admin, ModelView
from sqladmin.authentication import AuthenticationBackend
from sqladmin.fields import FileField
from starlette.requests import Request

from app.core.config import get_settings
from app.core.db import engine
from app.entities.audio_track import AudioTrack
from app.services.storage_service import get_storage
from app.services.track_service import TrackService


class AdminAuth(AuthenticationBackend):
    async def login(self, request: Request) -> bool:
        form = await request.form()
        settings = get_settings()
        username = str(form.get("username", ""))
        password = str(form.get("password", ""))
        if username == settings.admin_username and password == settings.admin_password:
            request.session.update({"admin": True})
            return True
        return False

    async def logout(self, request: Request) -> bool:
        request.session.clear()
        return True

    async def authenticate(self, request: Request) -> bool:
        return bool(request.session.get("admin"))


def _public_url_formatter(model: AudioTrack, attribute: str, request: Request) -> Markup:
    settings = get_settings()
    if not model.slug:
        return Markup("")
    url = f"{settings.public_base_url}/t/{model.slug}"
    return Markup(
        '<div class="d-flex align-items-center gap-2">'
        '<input class="form-control form-control-sm" readonly value="{url}" '
        'onclick="this.select()">'
        "</div>"
    ).format(url=url)


class AudioTrackAdmin(ModelView, model=AudioTrack):
    name = "Audio Track"
    name_plural = "Audio Tracks"
    icon = "fa-solid fa-headphones"

    column_list = [
        AudioTrack.id,
        AudioTrack.title,
        AudioTrack.slug,
        AudioTrack.author,
        AudioTrack.is_published,
        AudioTrack.location_name,
    ]
    column_details_list = [
        AudioTrack.id,
        AudioTrack.title,
        AudioTrack.slug,
        AudioTrack.description,
        AudioTrack.author,
        AudioTrack.audio_s3_key,
        AudioTrack.cover_s3_key,
        AudioTrack.latitude,
        AudioTrack.longitude,
        AudioTrack.location_name,
        AudioTrack.is_published,
        AudioTrack.published_at,
        AudioTrack.created_at,
        AudioTrack.updated_at,
    ]
    column_labels = {
        AudioTrack.slug: "Public URL (for NFC tag)",
    }
    column_formatters = {
        AudioTrack.slug: _public_url_formatter,
    }
    form_columns = [
        AudioTrack.title,
        AudioTrack.description,
        AudioTrack.author,
        AudioTrack.latitude,
        AudioTrack.longitude,
        AudioTrack.location_name,
        AudioTrack.is_published,
    ]

    async def scaffold_form(self, rules=None):
        Form = await super().scaffold_form(rules)
        return type(
            "AudioTrackForm",
            (Form,),
            {
                "audio_file": FileField("Audio file"),
                "cover_file": FileField("Cover image"),
            },
        )

    async def on_model_change(self, data, model, is_created, request):
        storage = get_storage()
        audio_file = data.get("audio_file")
        if audio_file and hasattr(audio_file, "filename") and audio_file.filename:
            key = f"audio/{secrets.token_urlsafe(12)}_{audio_file.filename}"
            content = await audio_file.read()
            storage.upload(key, content, audio_file.content_type or "audio/mpeg")
            if model.audio_s3_key:
                storage.delete(model.audio_s3_key)
            model.audio_s3_key = key

        cover_file = data.get("cover_file")
        if cover_file and hasattr(cover_file, "filename") and cover_file.filename:
            key = f"covers/{secrets.token_urlsafe(12)}_{cover_file.filename}"
            content = await cover_file.read()
            storage.upload(key, content, cover_file.content_type or "image/jpeg")
            if model.cover_s3_key:
                storage.delete(model.cover_s3_key)
            model.cover_s3_key = key

        if is_created:
            model.slug = TrackService.generate_slug()
        if data.get("is_published") and model.published_at is None:
            model.published_at = TrackService.now_utc()

        data.pop("audio_file", None)
        data.pop("cover_file", None)

    async def on_model_delete(self, model, request):
        storage = get_storage()
        if model.audio_s3_key:
            storage.delete(model.audio_s3_key)
        if model.cover_s3_key:
            storage.delete(model.cover_s3_key)


def setup_admin(app) -> None:
    admin = Admin(
        app,
        engine=engine,
        authentication_backend=AdminAuth(secret_key=get_settings().session_secret),
    )
    admin.add_view(AudioTrackAdmin)
