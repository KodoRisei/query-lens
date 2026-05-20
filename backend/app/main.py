from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

import structlog
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1 import api_router
from app.core.config import get_settings
from app.core.exceptions import (
    LLMProviderError,
    LLMProviderNotConfigured,
    QueryLensError,
    QueryTooLongError,
    SQLParseError,
)
from app.core.logging import configure_logging
from app.infrastructure.database.connection import dispose_engine, get_engine
from app.infrastructure.database.models import Base

configure_logging()
logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    logger.info(
        "application.startup",
        environment=settings.environment,
        debug=settings.debug,
    )
    async with get_engine().begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("database.tables.created")
    yield
    await dispose_engine()
    logger.info("application.shutdown")


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title="QueryLens API",
        description="AI-powered SQL review platform",
        version="0.1.0",
        docs_url="/docs" if not settings.is_production else None,
        redoc_url="/redoc" if not settings.is_production else None,
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(api_router, prefix=settings.api_v1_prefix)

    _register_exception_handlers(app)

    return app


def _register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(SQLParseError)
    async def sql_parse_error_handler(request: Request, exc: SQLParseError) -> JSONResponse:
        logger.warning("sql.parse.error", message=exc.message, details=exc.details)
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=_error_body("SQL_PARSE_ERROR", exc.message, exc.details),
        )

    @app.exception_handler(QueryTooLongError)
    async def query_too_long_handler(request: Request, exc: QueryTooLongError) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            content=_error_body(
                "QUERY_TOO_LONG",
                exc.message,
                {"length": exc.length, "max_length": exc.max_length},
            ),
        )

    @app.exception_handler(LLMProviderNotConfigured)
    async def provider_not_configured_handler(
        request: Request, exc: LLMProviderNotConfigured
    ) -> JSONResponse:
        logger.error("llm.provider.not_configured", provider=exc.provider)
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content=_error_body("LLM_PROVIDER_NOT_CONFIGURED", exc.message),
        )

    @app.exception_handler(LLMProviderError)
    async def llm_provider_error_handler(request: Request, exc: LLMProviderError) -> JSONResponse:
        logger.error(
            "llm.provider.error",
            provider=exc.provider,
            status_code=exc.status_code,
            message=exc.message,
        )
        return JSONResponse(
            status_code=status.HTTP_502_BAD_GATEWAY,
            content=_error_body("LLM_PROVIDER_ERROR", "AI provider request failed"),
        )

    @app.exception_handler(QueryLensError)
    async def generic_domain_error_handler(request: Request, exc: QueryLensError) -> JSONResponse:
        logger.error("domain.error", message=exc.message, details=exc.details)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=_error_body("INTERNAL_ERROR", "An unexpected error occurred"),
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("unhandled.exception", exc_info=exc)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=_error_body("INTERNAL_ERROR", "An unexpected error occurred"),
        )


def _error_body(code: str, message: str, details: Any = None) -> dict[str, Any]:
    body: dict[str, Any] = {"error": {"code": code, "message": message}}
    if details:
        body["error"]["details"] = details
    return body


app = create_app()
