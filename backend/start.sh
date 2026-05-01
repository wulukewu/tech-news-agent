#!/bin/bash

# Render startup script for tech-news-agent backend
# Optimized for faster startup and better health checks

set -e

echo "🚀 Starting Tech News Agent Backend..."

# Set default values if not provided
export PORT=${PORT:-8000}
export WORKERS=${WORKERS:-1}
export LOG_LEVEL=${LOG_LEVEL:-info}
export TIMEOUT_KEEP_ALIVE=${TIMEOUT_KEEP_ALIVE:-65}
export TIMEOUT_GRACEFUL_SHUTDOWN=${TIMEOUT_GRACEFUL_SHUTDOWN:-30}

# Pre-warm Python imports to reduce startup time
echo "📦 Pre-warming Python imports..."
python -c "
import asyncio
import uvicorn
from fastapi import FastAPI
from app.core.config import settings
print('✅ Core imports loaded')
"

# Start the application with optimized settings
echo "🌐 Starting FastAPI server on port $PORT..."
exec python -m uvicorn app.main:app \
  --host 0.0.0.0 \
  --port $PORT \
  --workers $WORKERS \
  --log-level $LOG_LEVEL \
  --timeout-keep-alive $TIMEOUT_KEEP_ALIVE \
  --timeout-graceful-shutdown $TIMEOUT_GRACEFUL_SHUTDOWN \
  --access-log \
  --no-use-colors
