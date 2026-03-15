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
import uvicorn

from app.core.config import settings
from app.bot.client import bot
from app.tasks.scheduler import scheduler, setup_scheduler

# Configure logging for the entire app
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("TechNewsAgent")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manage the lifecycle of background processes tied to FastAPI.
    Starts the APScheduler and the Discord Bot.
    """
    logger.info("Initializing Tech News Agent lifespan...")
    
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

if __name__ == "__main__":
    # Local testing entry point
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=False)
