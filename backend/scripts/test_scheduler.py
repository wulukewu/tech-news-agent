#!/usr/bin/env python3
"""
Test script to manually trigger the scheduler and see detailed error logs.
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from dotenv import load_dotenv

load_dotenv()

# Configure logging to show all levels
logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

from app.tasks.scheduler import scheduled_rss_fetch_and_analyze


async def main():
    """Run the scheduler task manually."""
    print("=" * 80)
    print("Starting manual scheduler test...")
    print("=" * 80)

    try:
        await scheduled_rss_fetch_and_analyze()
        print("\n" + "=" * 80)
        print("Scheduler completed successfully!")
        print("=" * 80)
    except Exception as e:
        print("\n" + "=" * 80)
        print(f"Scheduler failed with error: {e}")
        print("=" * 80)
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
