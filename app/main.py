import os
import sys

# Fix for macOS Python SSL Certificate Verification Error
if sys.platform == "darwin":
    import certifi
    os.environ["SSL_CERT_FILE"] = certifi.where()
    os.environ["SSL_CERT_DIR"] = os.path.dirname(certifi.where())

import logging
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, BackgroundTasks
from fastapi.responses import JSONResponse
import uvicorn

from app.core.config import settings
from app.core.exceptions import ConfigurationError
from app.bot.client import bot
from app.tasks.scheduler import scheduler, setup_scheduler, get_scheduler_health

# Configure logging for the entire app
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("TechNewsAgent")

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
        
    yield # The FastAPI app runs and serves requests here
    
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
    lifespan=lifespan
)

@app.get("/")
async def root():
    return {"status": "ok", "message": "Tech News Agent is running."}

@app.get("/health")
async def health_check():
    """Health check endpoint useful for Docker/Render deployments."""
    bot_ready = bot.is_ready() if settings.discord_token else False
    return {
        "status": "healthy",
        "bot_ready": bot_ready,
        "scheduler_running": scheduler.running
    }

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
    
    return JSONResponse(
        content=health_data,
        status_code=status_code
    )

if __name__ == "__main__":
    # Local testing entry point
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=False)
