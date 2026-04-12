import os
import sys

# Fix for macOS Python SSL Certificate Verification Error
if sys.platform == "darwin":
    import certifi

    os.environ["SSL_CERT_FILE"] = certifi.where()
    os.environ["SSL_CERT_DIR"] = os.path.dirname(certifi.where())

import asyncio
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api import (
    analytics,
    articles,
    auth,
    feeds,
    logs,
    onboarding,
    reading_list,
    recommendations,
)
from app.api import (
    scheduler as scheduler_api,
)
from app.bot.client import bot
from app.core.config import settings
from app.core.errors import (
    AppException,
    app_exception_handler,
    generic_exception_handler,
    http_exception_handler,
    validation_exception_handler,
)
from app.core.logger import RequestContextMiddleware, get_logger
from app.tasks.scheduler import get_scheduler_health, scheduler, setup_scheduler

# Use centralized structured logger
logger = get_logger(__name__)


def validate_configuration():
    """Validate required configuration settings."""
    # Supabase configuration is validated by Pydantic Settings (required fields)
    # Discord and LLM configuration is validated at runtime when services are used
    pass


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manage the lifecycle of background processes tied to FastAPI.
    Starts the APScheduler and the Discord Bot.
    """
    logger.info("Initializing Tech News Agent lifespan...")

    # Validate configuration before starting services
    validate_configuration()
    logger.info("Configuration validated successfully.")

    # 1. Start the Scheduler
    setup_scheduler()
    scheduler.start()
    logger.info("Scheduler started.")

    # 2. Start the Discord Bot in the background
    bot_task = None
    if settings.discord_token:
        logger.info("Starting Discord Bot in background...")
        # create_task ensures it doesn't block FastAPI startup
        bot_task = asyncio.create_task(bot.start(settings.discord_token))

        def handle_bot_error(task: asyncio.Task):
            try:
                task.result()
            except asyncio.CancelledError:
                pass
            except Exception as e:
                logger.error(f"Discord Bot background task failed: {e}", exc_info=True)

        bot_task.add_done_callback(handle_bot_error)
    else:
        logger.warning("No DISCORD_TOKEN found. Bot will not start.")

    yield  # The FastAPI app runs and serves requests here

    logger.info("Shutting down Tech News Agent lifespan...")

    # Shutdown Scheduler
    scheduler.shutdown(wait=False)

    # Shutdown Discord Bot
    if bot_task and not bot_task.done():
        logger.info("Closing Discord Bot connection...")
        await bot.close()
        await bot_task


# FastAPI Instance
app = FastAPI(
    title="Tech News Agent",
    description="Automated RSS Curation Engine running with Discord Bot",
    version="1.0.0",
    lifespan=lifespan,
)

# Configure CORS Middleware
cors_origins = (
    settings.cors_origins.split(",") if settings.cors_origins else ["http://localhost:3000"]
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
    expose_headers=["Set-Cookie"],
)

# Add Request Context Middleware for structured logging
app.add_middleware(RequestContextMiddleware)

# Register Exception Handlers
app.add_exception_handler(AppException, app_exception_handler)
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)

# Configure Rate Limiting
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


# Security Headers Middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    """Add security headers to all responses."""
    # Handle OPTIONS requests for CORS preflight
    if request.method == "OPTIONS":
        response = JSONResponse(content={}, status_code=200)
        response.headers["Access-Control-Allow-Origin"] = request.headers.get("origin", "*")
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, PATCH, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
        response.headers["Access-Control-Allow-Credentials"] = "true"
        return response

    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    return response


# Register API routers
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(feeds.router, prefix="/api", tags=["feeds"])
app.include_router(articles.router, prefix="/api/articles", tags=["articles"])
app.include_router(reading_list.router, prefix="/api", tags=["reading-list"])
app.include_router(scheduler_api.router, prefix="/api", tags=["scheduler"])
app.include_router(onboarding.router, prefix="/api", tags=["onboarding"])
app.include_router(recommendations.router, prefix="/api", tags=["recommendations"])
app.include_router(analytics.router, prefix="/api", tags=["analytics"])
app.include_router(logs.router, tags=["logs"])


@app.get("/")
async def root():
    return {"status": "ok", "message": "Tech News Agent is running."}


@app.get("/health")
async def health_check():
    """
    Health check endpoint useful for Docker/Render deployments.
    Includes OAuth2 and JWT configuration validation.

    Validates: Requirements 20.1, 20.2, 20.3, 20.4, 20.5, 20.6, 20.7
    """
    bot_ready = bot.is_ready() if settings.discord_token else False

    # Initialize health status
    health_status = {
        "status": "healthy",
        "services": {
            "bot": "healthy" if bot_ready else "degraded",
            "scheduler": "healthy" if scheduler.running else "degraded",
            "database": "healthy",
            "oauth": "healthy",
            "jwt": "healthy",
        },
    }

    # Check OAuth2 configuration
    if not all(
        [settings.discord_client_id, settings.discord_client_secret, settings.discord_redirect_uri]
    ):
        health_status["services"]["oauth"] = "unhealthy"
        health_status["status"] = "degraded"

    # Check JWT configuration
    if not settings.jwt_secret or len(settings.jwt_secret) < 32:
        health_status["services"]["jwt"] = "unhealthy"
        health_status["status"] = "degraded"

    # Check database connectivity (basic check)
    try:
        from app.services.supabase_service import SupabaseService

        # Connection validation happens in __init__
        _ = SupabaseService()
    except Exception:
        health_status["services"]["database"] = "unhealthy"
        health_status["status"] = "degraded"

    # Determine overall status code
    status_code = 200
    if health_status["status"] == "unhealthy":
        status_code = 503

    return JSONResponse(content=health_status, status_code=status_code)


@app.get("/health/scheduler")
async def scheduler_health_check():
    """
    Scheduler-specific health check endpoint.

    Returns:
        - 200: Scheduler is healthy
        - 503: Scheduler is unhealthy (not run in 12 hours or >50% failure rate)

    Validates: Requirements 10.1, 10.2, 10.3, 10.4, 10.5, 10.6, 10.7
    """
    health_data = await get_scheduler_health()
    status_code = health_data.pop("status_code")

    return JSONResponse(content=health_data, status_code=status_code)


if __name__ == "__main__":
    # Local testing entry point
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=False)
