from litestar import MediaType, Request, Response
from litestar.datastructures import State
from litestar.status_codes import (
    HTTP_400_BAD_REQUEST,
    HTTP_401_UNAUTHORIZED,
    HTTP_403_FORBIDDEN,
    HTTP_404_NOT_FOUND,
    HTTP_409_CONFLICT,
    HTTP_503_SERVICE_UNAVAILABLE,
)

from app.lib.schema import CamelizedBaseStruct


class ApplicationError(Exception):
    status_code: int = HTTP_400_BAD_REQUEST
    default_code: str = "bad_request"

    def __init__(self, detail: str, code: str | None = None) -> None:
        super().__init__(detail)
        self.detail = detail
        self.code = code or self.default_code


class BadRequestError(ApplicationError):
    pass


class UnauthorizedError(ApplicationError):
    status_code = HTTP_401_UNAUTHORIZED
    default_code = "unauthorized"


class ForbiddenError(ApplicationError):
    status_code = HTTP_403_FORBIDDEN
    default_code = "forbidden"


class NotFoundError(ApplicationError):
    status_code = HTTP_404_NOT_FOUND
    default_code = "not_found"


class ConflictError(ApplicationError):
    status_code = HTTP_409_CONFLICT
    default_code = "conflict"


class ServiceUnavailableError(ApplicationError):
    status_code = HTTP_503_SERVICE_UNAVAILABLE
    default_code = "service_unavailable"


class ErrorBody(CamelizedBaseStruct):
    detail: str
    code: str


def application_error_handler(
    request: Request[object, object, State], exc: ApplicationError
) -> Response[ErrorBody]:
    return Response(
        content=ErrorBody(detail=exc.detail, code=exc.code),
        status_code=exc.status_code,
        media_type=MediaType.JSON,
    )
