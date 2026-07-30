"""
Application entrypoint.

Wires together configuration, logging, middleware, routers, and global
exception handling into a single FastAPI application instance.
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.exception_handlers import register_exception_handlers
from app.core.logging import configure_logging, get_logger
from app.db.session import SessionLocal
from app.middleware.request_logging import RequestLoggingMiddleware

configure_logging()
logger = get_logger("app.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown lifecycle handler."""
    logger.info(
        "startup project=%s version=%s environment=%s",
        settings.PROJECT_NAME,
        settings.VERSION,
        settings.ENVIRONMENT,
    )
    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        logger.info("database_connection_verified")
    except Exception as exc:  # noqa: BLE001
        logger.error("database_connection_failed error=%s", str(exc))

    yield

    logger.info("shutdown project=%s", settings.PROJECT_NAME)


def create_application() -> FastAPI:
    """Application factory that assembles and configures the FastAPI app."""
    app = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
        docs_url=f"{settings.API_V1_PREFIX}/docs",
        redoc_url=f"{settings.API_V1_PREFIX}/redoc",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.BACKEND_CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(RequestLoggingMiddleware)

    register_exception_handlers(app)

    app.include_router(api_router, prefix=settings.API_V1_PREFIX)

    @app.get("/", status_code=status.HTTP_200_OK, tags=["Root"])
    def root() -> dict[str, str]:
        """Top-level root endpoint."""
        return {"project": settings.PROJECT_NAME, "version": settings.VERSION}

    @app.get("/health", status_code=status.HTTP_200_OK, tags=["Health"])
    def health() -> dict[str, str]:
        """Top-level infrastructure health check (used by orchestrators)."""
        return {"status": "healthy"}

    return app


app = create_application()
