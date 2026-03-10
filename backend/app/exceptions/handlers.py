"""전역 예외 핸들러 함수 정의."""

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.exceptions.business import BusinessException
from app.schemas.common import ApiResponse


async def business_exception_handler(request: Request, exc: BusinessException) -> JSONResponse:
    """비즈니스 예외 핸들러."""
    request.state.error_message = f"[{exc.__class__.__name__}] {exc.message}"
    return JSONResponse(
        status_code=exc.status_code,
        content=ApiResponse.fail(
            message=exc.message,
            code=exc.__class__.__name__,
            path=str(request.url.path),
        ).model_dump(),
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """바디, 쿼리, 패스, 헤더 검증 예외 핸들러."""
    request.state.error_message = f"[VALIDATION_ERROR] {exc.errors()}"
    return JSONResponse(
        status_code=400,
        content=ApiResponse.fail(
            code="VALIDATION_ERROR",
            message="요청 값이 올바르지 않습니다.",
        ).model_dump(),
    )


async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """전역 예외 핸들러 — 처리되지 않은 모든 예외."""
    request.state.error_message = f"[{exc.__class__.__name__}] {str(exc)}"
    return JSONResponse(
        status_code=500,
        content=ApiResponse.fail(
            message="Unexpected Exception",
            code="InternalServerError",
            path=str(request.url.path),
        ).model_dump(),
    )
