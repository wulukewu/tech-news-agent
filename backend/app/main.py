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
from app.tasks.scheduler import get_scheduler, get_scheduler_health, setup_scheduler

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

    # 0. Initialize QA Agent Database Manager
    try:
        # Only attempt direct PostgreSQL if explicitly configured via DATABASE_URL or DATABASE_HOST.
        # Without explicit config, the auto-derived db.<project>.supabase.co:5432 is blocked
        # in most network environments (including Docker). Default to Supabase REST API.
        use_direct_pg = bool(settings.database_url or settings.database_host)

        if use_direct_pg:
            try:
                from app.qa_agent.database import get_database_manager

                logger.info("Initializing QA Agent database manager (PostgreSQL)...")
                db_manager = await get_database_manager()
                health = await db_manager.health_check()
                if health["healthy"]:
                    logger.info("QA Agent database manager (PostgreSQL) initialized successfully.")
                else:
                    raise Exception(f"PostgreSQL health check failed: {health}")
            except Exception as pg_error:
                logger.warning(
                    f"PostgreSQL connection failed, falling back to Supabase REST API: {pg_error}"
                )
                use_direct_pg = False

        if not use_direct_pg:
            from app.qa_agent.supabase_database import get_supabase_database_manager

            logger.info("Initializing QA Agent database manager (Supabase REST API)...")
            supabase_db_manager = await get_supabase_database_manager()
            health = await supabase_db_manager.health_check()
            if health["healthy"]:
                logger.info(
                    "QA Agent database manager (Supabase REST API) initialized successfully."
                )
            else:
                raise Exception(f"Supabase health check failed: {health}")
    except Exception as e:
        logger.error(f"Failed to initialize any QA Agent database manager: {e}", exc_info=True)
        # Don't fail startup - QA features will be disabled but other features work

    # 1. Start the Scheduler
    if settings.enable_scheduler:
        try:
            setup_scheduler()
            scheduler = get_scheduler()
            if scheduler is None:
                raise RuntimeError(
                    "Scheduler initialization failed - scheduler is None after setup"
                )
            scheduler.start()
            logger.info("Scheduler started successfully.")
        except Exception as e:
            logger.error(f"Failed to start scheduler: {e}", exc_info=True)
            raise
    else:
        logger.info("Scheduler disabled via ENABLE_SCHEDULER=false")

    # 2. Initialize notification system integration
    try:
        from app.services.notification_monitoring import initialize_notification_monitoring_service
        from app.services.notification_system_integration import (
            initialize_notification_system_integration,
        )
        from app.services.preference_synchronization_service import (
            initialize_preference_sync_service,
        )
        from app.services.supabase_service import SupabaseService
        from app.services.system_initialization import initialize_personalized_notification_system
        from app.tasks.scheduler import get_dynamic_scheduler

        # Get required services
        dynamic_scheduler = get_dynamic_scheduler()
        supabase_service = SupabaseService()

        # Initialize the integrated notification system
        integration_service = initialize_notification_system_integration(
            supabase_service=supabase_service,
            dynamic_scheduler=dynamic_scheduler,
            bot_client=bot,  # Pass the Discord bot client
        )

        logger.info("Notification system integration initialized successfully.")

        # Initialize monitoring service
        monitoring_service = initialize_notification_monitoring_service(supabase_service)
        await monitoring_service.start_monitoring()
        logger.info("Notification monitoring service initialized and started.")

        # Also initialize the legacy preference sync service for backward compatibility
        initialize_preference_sync_service(dynamic_scheduler)
        logger.info(
            "Legacy preference synchronization service initialized for backward compatibility."
        )

        # Restore all user notification schedules from database
        # This ensures schedules persist across service restarts
        try:
            logger.info("Restoring user notification schedules from database...")
            restore_stats = await dynamic_scheduler.restore_all_user_schedules()
            logger.info(
                f"User notification schedules restored: "
                f"{restore_stats['restored']} restored, "
                f"{restore_stats['skipped']} skipped, "
                f"{restore_stats['failed']} failed"
            )
        except Exception as e:
            logger.error(f"Failed to restore user notification schedules: {e}", exc_info=True)
            # Don't fail the entire startup if restoration fails
            # Individual users can manually reschedule if needed

        # Initialize the personalized notification system (migrate users, start scheduling)
        logger.info("Starting personalized notification system initialization...")
        init_results = await initialize_personalized_notification_system(supabase_service)

        if init_results.get("success", False):
            logger.info(
                "Personalized notification system initialization completed successfully",
                migrated_users=init_results.get("migration", {}).get("migrated_count", 0),
                scheduled_users=init_results.get("scheduling", {}).get("scheduled_count", 0),
            )
        else:
            logger.warning(
                "Personalized notification system initialization completed with issues",
                results=init_results,
            )

    except Exception as e:
        logger.error(f"Failed to initialize notification system integration: {e}", exc_info=True)
        # Don't raise here as this is not critical for basic functionality

    # 3. Start the Discord Bot in the background
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

    # Shutdown QA Agent Database Manager
    try:
        # Try to close both possible database managers
        try:
            from app.qa_agent.database import close_database_manager

            await close_database_manager()
            logger.info("QA Agent database manager (PostgreSQL) closed.")
        except:
            pass

        try:
            from app.qa_agent.supabase_database import close_supabase_database_manager

            await close_supabase_database_manager()
            logger.info("QA Agent database manager (Supabase) closed.")
        except:
            pass
    except Exception as e:
        logger.error(f"Error closing QA Agent database managers: {e}")

    # Shutdown monitoring service
    try:
        from app.services.notification_monitoring import get_notification_monitoring_service

        monitoring_service = get_notification_monitoring_service()
        if monitoring_service:
            await monitoring_service.stop_monitoring()
            logger.info("Notification monitoring service stopped.")
    except Exception as e:
        logger.error(f"Error stopping monitoring service: {e}")

    # Shutdown Scheduler
    scheduler = get_scheduler()
    if scheduler is not None:
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

# Import and register notifications router
from app.api import notifications

app.include_router(notifications.router, prefix="/api/notifications", tags=["notifications"])

# Import and register learning path router
from app.api import learning_path

app.include_router(learning_path.router, tags=["learning-path"])

# Import and register notification system router
from app.api import notification_system

app.include_router(
    notification_system.router, prefix="/api/notification-system", tags=["notification-system"]
)

# Import and register debug router (for development)
from app.api import debug

app.include_router(debug.router, prefix="/api", tags=["debug"])

# Import and register QA router
from app.api import qa as qa_api

app.include_router(qa_api.router, prefix="/api/qa", tags=["qa"])

# Import and register Conversations router
from app.api import conversations as conversations_api

app.include_router(conversations_api.router, prefix="/api/conversations", tags=["conversations"])

# Import and register Weekly Insights router
from app.api import weekly_insights as weekly_insights_api

app.include_router(weekly_insights_api.router, prefix="/api", tags=["weekly-insights"])

# Import and register Proactive Learning router
from app.api import proactive_learning as proactive_learning_api

app.include_router(proactive_learning_api.router, prefix="/api", tags=["proactive-learning"])

# Import and register Platforms router (user platform linking + sync)
from app.api import platforms as platforms_api

app.include_router(platforms_api.router, prefix="/api/user/platforms", tags=["platforms"])
# Also mount the conversation sync endpoint under /api
app.include_router(
    platforms_api.router, prefix="/api", tags=["conversations"], include_in_schema=False
)


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

    # Get scheduler instance
    scheduler = get_scheduler()

    # Check QA Agent health
    qa_agent_status = "healthy"
    try:
        from app.qa_agent.simple_qa import get_simple_qa_agent  # noqa: F401

        # Just check if we can import it
        _ = get_simple_qa_agent()
    except Exception:
        qa_agent_status = "degraded"

    # Initialize health status
    health_status = {
        "status": "healthy",
        "services": {
            "bot": "healthy" if bot_ready else "degraded",
            "scheduler": "healthy" if (scheduler and scheduler.running) else "degraded",
            "database": "healthy",
            "oauth": "healthy",
            "jwt": "healthy",
            "qa_agent": qa_agent_status,
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
