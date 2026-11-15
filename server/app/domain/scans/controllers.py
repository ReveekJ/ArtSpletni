from typing import Annotated

import msgspec
from litestar import Controller, post
from litestar.di import NamedDependency, Provide
from litestar.params import JSONBody
from litestar.status_codes import HTTP_200_OK

from app.config import rate_limit
from app.domain.auth.session import bind_user
from app.domain.points.content_service import PointContentService
from app.domain.points.deps import provide_point_content_service
from app.domain.runs.deps import (
    provide_progress_bus,
    provide_progress_listeners,
    provide_run_presenter,
    provide_run_service,
    provide_scan_service,
)
from app.domain.runs.schemas import NextStopOut, RunPresenter, ScanResponse
from app.domain.scans.services import ScanResult, ScanService
from app.lib.i18n import resolve_text
from app.lib.request import AppRequest
from app.lib.schema import CamelizedBaseStruct

SCAN_RATE_LIMIT = rate_limit("scan", "minute", 30)


class ScanInput(CamelizedBaseStruct):
    token: Annotated[str, msgspec.Meta(min_length=16, max_length=128)]


class ScanController(Controller):
    path = "/api/scans"
    tags = ["Scans"]
    dependencies = {
        "progress_listeners": Provide(provide_progress_listeners),
        "progress_bus": Provide(provide_progress_bus),
        "run_service": Provide(provide_run_service),
        "scan_service": Provide(provide_scan_service),
        "run_presenter": Provide(provide_run_presenter),
        "point_content_service": Provide(provide_point_content_service),
    }

    @post(
        "/",
        summary="Scan NFC tag",
        description=(
            "Resolve an NFC tag token, unlock its point and advance route progress. "
            "Creates a guest session for anonymous visitors."
        ),
        status_code=HTTP_200_OK,
        middleware=[SCAN_RATE_LIMIT.middleware],
    )
    async def scan(
        self,
        request: AppRequest,
        data: JSONBody[ScanInput],
        scan_service: NamedDependency[ScanService],
        run_presenter: NamedDependency[RunPresenter],
        point_content_service: NamedDependency[PointContentService],
    ) -> ScanResponse:
        result = await scan_service.scan(data.token, request.user)
        if result.user is not None and request.user is None:
            bind_user(request, result.user)
        return await _to_response(result, run_presenter, point_content_service)


async def _to_response(
    result: ScanResult, presenter: RunPresenter, content: PointContentService
) -> ScanResponse:
    cards = await content.cards([result.point]) if result.point else {}
    return ScanResponse(
        outcome=result.outcome,
        point=cards.get(result.point.id) if result.point else None,
        content_available=result.content_available,
        run=presenter.run_state(result.route, result.run) if result.route and result.run else None,
        candidates=[presenter.candidate(candidate) for candidate in result.candidates],
        next_stops=[
            NextStopOut(
                point_id=item.point.id if item.show_point and item.point else None,
                title=resolve_text(item.point.title, presenter.language, presenter.fallback)
                if item.show_point and item.point
                else None,
                hint=resolve_text(item.stop.hint, presenter.language, presenter.fallback),
            )
            for item in result.next_stops
        ],
        notifications=result.notifications,
    )
