"""Medical Appointment and Reminder System - FastAPI application."""

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.responses import Response
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.sessions import SessionMiddleware

from app.api import api_v1_router
from app.auth.middleware import AuthMiddleware
from app.auth.user_context import UserContextMiddleware
from app.config import get_settings
from app.database import Base, engine
from app.models import (  # noqa: F401 - register all models
    Admin,
    Appointment,
    AppointmentStatusHistory,
    Doctor,
    DoctorAvailability,
    DoctorReview,
    Notification,
    PasswordResetToken,
    Payment,
    Specialization,
    User,
)
from app.routes import auth_router, dashboard_router, web_router
from app.scheduler import shutdown_scheduler, start_scheduler
from app.utils import AppException

settings = get_settings()

logging.basicConfig(
    level=logging.DEBUG if settings.debug else logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown lifecycle hooks."""
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    Base.metadata.create_all(bind=engine)
    start_scheduler()
    logger.info("%s is running at http://%s:%s", settings.app_name, settings.host, settings.port)
    yield
    shutdown_scheduler()


class NoCacheStaticFiles(StaticFiles):
    """Serve static assets with no-cache headers in debug to avoid stale JS/CSS."""

    async def get_response(self, path: str, scope) -> Response:
        response = await super().get_response(path, scope)
        if settings.debug and path and path.endswith((".js", ".css")):
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
            response.headers["Pragma"] = "no-cache"
        return response


def create_app() -> FastAPI:
    """Application factory."""
    app = FastAPI(
        title=settings.app_name,
        description="Healthcare appointment management and reminder platform",
        version="0.1.0",
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json",
        lifespan=lifespan,
    )

    # Middleware - last added runs first (outermost)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"] if settings.debug else [],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(AuthMiddleware)
    app.add_middleware(UserContextMiddleware)
    app.add_middleware(
        SessionMiddleware,
        secret_key=settings.secret_key,
        max_age=settings.session_max_age,
    )

    static_path = Path(settings.static_dir)
    static_path.mkdir(parents=True, exist_ok=True)
    app.mount("/static", NoCacheStaticFiles(directory=str(static_path)), name="static")

    app.include_router(web_router)
    app.include_router(auth_router)
    app.include_router(dashboard_router)
    app.include_router(api_v1_router)

    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException):
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        return JSONResponse(status_code=422, content={"detail": exc.errors()})

    return app


app = create_app()
