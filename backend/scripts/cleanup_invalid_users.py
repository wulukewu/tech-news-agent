#!/usr/bin/env python3
"""
Cleanup script to remove invalid Discord IDs from the database.

This script removes users with invalid discord_id formats:
- Non-numeric discord_ids (e.g., test_user_abc123)
- Discord IDs exceeding the maximum snowflake value (9223372036854775807)
"""

import asyncio
import logging
import os
import sys
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from supabase import create_client

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def cleanup_invalid_users():
    """Remove users with invalid discord_id formats."""

    # Get Supabase credentials
    supabase_url = os.getenv("SUPABASE_URL")
    # Try both variable names for compatibility
    supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_KEY")

    if not supabase_url or not supabase_key:
        logger.error("Missing SUPABASE_URL or SUPABASE_KEY environment variables")
        return

    # Create Supabase client
    client = create_client(supabase_url, supabase_key)

    try:
        # Fetch all users
        logger.info("Fetching all users from database...")
        response = client.table("users").select("id, discord_id").execute()
        all_users = response.data

        logger.info(f"Found {len(all_users)} total users")

        invalid_users = []

        # Check each user's discord_id
        for user in all_users:
            discord_id = user["discord_id"]
            user_id = user["id"]

            # Check if discord_id is numeric
            if not discord_id.isdigit():
                invalid_users.append(
                    {"id": user_id, "discord_id": discord_id, "reason": "non-numeric"}
                )
                continue

            # Check if discord_id exceeds max snowflake value
            try:
                discord_id_int = int(discord_id)
                if discord_id_int > 9223372036854775807:
                    invalid_users.append(
                        {"id": user_id, "discord_id": discord_id, "reason": "exceeds_max_value"}
                    )
            except ValueError:
                invalid_users.append(
                    {"id": user_id, "discord_id": discord_id, "reason": "invalid_integer"}
                )

        if not invalid_users:
            logger.info("No invalid users found!")
            return

        logger.info(f"Found {len(invalid_users)} invalid users:")
        for user in invalid_users[:10]:  # Show first 10
            logger.info(f"  - {user['discord_id']} (reason: {user['reason']})")

        if len(invalid_users) > 10:
            logger.info(f"  ... and {len(invalid_users) - 10} more")

        # Ask for confirmation
        print("\n⚠️  This will DELETE all invalid users from the database.")
        print("   Related data (subscriptions, reading lists, etc.) will be cascade deleted.")
        response = input("\nProceed with deletion? (yes/no): ")

        if response.lower() != "yes":
            logger.info("Deletion cancelled by user")
            return

        # Delete invalid users
        logger.info("Deleting invalid users...")
        deleted_count = 0

        for user in invalid_users:
            try:
                client.table("users").delete().eq("id", user["id"]).execute()
                deleted_count += 1

                if deleted_count % 10 == 0:
                    logger.info(f"Deleted {deleted_count}/{len(invalid_users)} users...")
            except Exception as e:
                logger.error(f"Failed to delete user {user['discord_id']}: {e}")

        logger.info(f"✅ Successfully deleted {deleted_count} invalid users")

    except Exception as e:
        logger.error(f"Error during cleanup: {e}", exc_info=True)


if __name__ == "__main__":
    asyncio.run(cleanup_invalid_users())
