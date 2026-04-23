#!/usr/bin/env python3
"""
Chat Persistence Database Initialisation Script

Reads and displays the SQL migration files for the chat persistence system,
checks whether the required tables already exist, and optionally inserts
sample seed data for development.

Usage:
    # Show migration instructions (default)
    python backend/scripts/init_chat_db.py

    # Also insert sample seed data after confirming tables exist
    python backend/scripts/init_chat_db.py --seed

    # Skip the prerequisite connectivity check
    python backend/scripts/init_chat_db.py --skip-check

Because Supabase restricts direct DDL execution via the REST API, the SQL
migrations must be applied manually through the Supabase Dashboard SQL Editor.
This script prints the SQL content and guides the operator through the process.

Validates: Requirements 7.1, 8.5
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from uuid import uuid4

# ---------------------------------------------------------------------------
# Path bootstrap — allow running from any working directory
# ---------------------------------------------------------------------------
_BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_BACKEND_DIR))

from dotenv import load_dotenv

# Load .env from backend/ or project root
_env_candidates = [_BACKEND_DIR / ".env", _BACKEND_DIR.parent / ".env"]
for _env_path in _env_candidates:
    if _env_path.exists():
        load_dotenv(_env_path)
        break

from app.core.database import MIGRATION_FILES, check_chat_tables_health, get_migration_version
from app.core.logger import get_logger

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_MIGRATIONS_DIR = _BACKEND_DIR / "scripts" / "migrations"

#: Tables that must exist for the chat persistence system to be operational.
_REQUIRED_TABLES = [
    "conversations",
    "conversation_messages",
    "user_platform_links",
    "conversation_tags",
]

# ---------------------------------------------------------------------------
# Helper utilities
# ---------------------------------------------------------------------------


def _separator(char: str = "=", width: int = 72) -> str:
    return char * width


def _print_section(title: str) -> None:
    print()
    print(_separator())
    print(title)
    print(_separator())


def _build_supabase_client():
    """Create and return a Supabase client using environment variables.

    Returns:
        A Supabase ``Client`` instance, or ``None`` if credentials are missing.
    """
    from supabase import create_client

    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY") or os.getenv("SUPABASE_SERVICE_ROLE_KEY")

    if not url or not key:
        logger.warning("SUPABASE_URL or SUPABASE_KEY not set — skipping connectivity check")
        return None

    try:
        client = create_client(url, key)
        logger.info("Supabase client created successfully")
        return client
    except Exception as exc:
        logger.error("Failed to create Supabase client", error=str(exc))
        return None


def _table_exists(client, table_name: str) -> bool:
    """Return ``True`` if *table_name* is accessible via the Supabase client."""
    try:
        client.table(table_name).select("*").limit(0).execute()
        return True
    except Exception:
        return False


# ---------------------------------------------------------------------------
# Core steps
# ---------------------------------------------------------------------------


def check_prerequisites(client) -> dict[str, bool]:
    """Check which required tables already exist.

    Args:
        client: An initialised Supabase ``Client`` instance.

    Returns:
        A dict mapping each table name to a boolean (``True`` = exists).
    """
    _print_section("STEP 1 — Checking existing tables")

    status: dict[str, bool] = {}
    for table in _REQUIRED_TABLES:
        exists = _table_exists(client, table)
        status[table] = exists
        icon = "✅" if exists else "❌"
        print(f"  {icon}  {table}")

    existing = [t for t, ok in status.items() if ok]
    missing = [t for t, ok in status.items() if not ok]

    print()
    if missing:
        print(f"  Tables to create : {', '.join(missing)}")
    else:
        print("  All required tables already exist.")

    return status


def show_migration_instructions(table_status: dict[str, bool]) -> None:
    """Print the SQL migration content and manual application instructions.

    Only migrations whose tables are not yet present are shown.  If all
    tables already exist the function prints a short confirmation and returns.

    Args:
        table_status: Mapping of table name → exists (from
            :func:`check_prerequisites`).
    """
    all_present = all(table_status.values())

    _print_section("STEP 2 — Migration SQL")

    if all_present:
        print("  All tables are already present — no migrations need to be applied.")
        return

    # Check which migration files exist on disk
    version_map = get_migration_version(str(_MIGRATIONS_DIR))

    print("  Because Supabase restricts direct DDL via the REST API, migrations")
    print("  must be applied manually through the Supabase Dashboard SQL Editor.")
    print()
    print("  Steps:")
    print("    1. Open https://supabase.com/dashboard and select your project.")
    print("    2. Navigate to  SQL Editor.")
    print("    3. For each migration file listed below, create a new query,")
    print("       paste the SQL, and click  Run.")
    print("    4. Re-run this script to verify the tables were created.")
    print()

    for migration_file in MIGRATION_FILES:
        migration_path = _MIGRATIONS_DIR / migration_file
        present_on_disk = version_map.get(migration_file, False)

        print(_separator("-"))
        print(f"  Migration file : {migration_file}")
        print(f"  Path           : {migration_path}")
        print(f"  File on disk   : {'yes' if present_on_disk else 'NOT FOUND'}")
        print(_separator("-"))

        if not present_on_disk:
            print(f"  ⚠️  File not found: {migration_path}")
            print()
            continue

        try:
            sql_content = migration_path.read_text(encoding="utf-8")
            print()
            print(sql_content)
            print()
        except OSError as exc:
            print(f"  ❌  Could not read file: {exc}")
            print()


def run_health_check(client) -> bool:
    """Run the full chat database health check and print a summary.

    Args:
        client: An initialised Supabase ``Client`` instance.

    Returns:
        ``True`` if all tables are healthy, ``False`` otherwise.
    """
    import asyncio

    _print_section("STEP 3 — Health Check")

    health = asyncio.run(check_chat_tables_health(client))

    for table_name, result in health.tables.items():
        icon = "✅" if result.accessible else "❌"
        row_info = f"  (rows: {result.row_count})" if result.row_count is not None else ""
        print(f"  {icon}  {table_name}{row_info}")
        if result.error:
            print(f"       Error: {result.error}")

    print()
    if health.healthy:
        print("  ✅  All chat persistence tables are healthy.")
    else:
        print("  ❌  Some tables are not accessible.  Apply the migrations above first.")
        for err in health.errors:
            print(f"       • {err}")

    return health.healthy


def insert_seed_data(client) -> None:
    """Insert sample data for development and testing.

    Creates one sample conversation, two messages, one platform link, and
    one tag — all associated with a synthetic user UUID so they can be
    identified and cleaned up easily.

    Args:
        client: An initialised Supabase ``Client`` instance.
    """
    _print_section("STEP 4 — Seed Data (development only)")

    # Use a fixed seed user UUID so repeated runs are idempotent
    seed_user_id = "00000000-0000-0000-0000-000000000001"
    seed_conversation_id = str(uuid4())

    print(f"  Seed user ID        : {seed_user_id}")
    print(f"  Seed conversation ID: {seed_conversation_id}")
    print()

    created: list[str] = []
    skipped: list[str] = []
    errors: list[str] = []

    # ------------------------------------------------------------------
    # 1. Seed conversation
    # ------------------------------------------------------------------
    try:
        existing = (
            client.table("conversations")
            .select("id")
            .eq("user_id", seed_user_id)
            .limit(1)
            .execute()
        )
        if existing.data:
            skipped.append("conversations (seed row already exists)")
        else:
            client.table("conversations").insert(
                {
                    "id": seed_conversation_id,
                    "user_id": seed_user_id,
                    "title": "Sample Conversation (seed)",
                    "summary": "A sample conversation created by the init script for development.",
                    "platform": "web",
                    "tags": ["sample", "seed"],
                    "is_archived": False,
                    "is_favorite": False,
                    "message_count": 0,
                    "metadata": {"source": "init_chat_db.py"},
                }
            ).execute()
            created.append("conversations")
    except Exception as exc:
        errors.append(f"conversations: {exc}")

    # ------------------------------------------------------------------
    # 2. Seed messages
    # ------------------------------------------------------------------
    try:
        existing_msgs = (
            client.table("conversation_messages")
            .select("id")
            .eq("conversation_id", seed_conversation_id)
            .limit(1)
            .execute()
        )
        if existing_msgs.data:
            skipped.append("conversation_messages (seed rows already exist)")
        else:
            client.table("conversation_messages").insert(
                [
                    {
                        "conversation_id": seed_conversation_id,
                        "role": "user",
                        "content": "Hello! This is a sample user message.",
                        "platform": "web",
                        "metadata": {},
                    },
                    {
                        "conversation_id": seed_conversation_id,
                        "role": "assistant",
                        "content": "Hello! This is a sample assistant response.",
                        "platform": "web",
                        "metadata": {},
                    },
                ]
            ).execute()
            created.append("conversation_messages (2 rows)")
    except Exception as exc:
        errors.append(f"conversation_messages: {exc}")

    # ------------------------------------------------------------------
    # 3. Seed platform link
    # ------------------------------------------------------------------
    try:
        existing_link = (
            client.table("user_platform_links")
            .select("user_id")
            .eq("user_id", seed_user_id)
            .eq("platform", "discord")
            .limit(1)
            .execute()
        )
        if existing_link.data:
            skipped.append("user_platform_links (seed row already exists)")
        else:
            client.table("user_platform_links").insert(
                {
                    "user_id": seed_user_id,
                    "platform": "discord",
                    "platform_user_id": "123456789012345678",
                    "platform_username": "seed_user#0001",
                    "is_active": True,
                    "verification_data": {"source": "init_chat_db.py"},
                }
            ).execute()
            created.append("user_platform_links")
    except Exception as exc:
        errors.append(f"user_platform_links: {exc}")

    # ------------------------------------------------------------------
    # 4. Seed tag
    # ------------------------------------------------------------------
    try:
        existing_tag = (
            client.table("conversation_tags")
            .select("id")
            .eq("user_id", seed_user_id)
            .eq("tag_name", "sample")
            .limit(1)
            .execute()
        )
        if existing_tag.data:
            skipped.append("conversation_tags (seed row already exists)")
        else:
            client.table("conversation_tags").insert(
                {
                    "user_id": seed_user_id,
                    "tag_name": "sample",
                    "color": "#3B82F6",
                    "usage_count": 1,
                }
            ).execute()
            created.append("conversation_tags")
    except Exception as exc:
        errors.append(f"conversation_tags: {exc}")

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------
    print("  Created :")
    if created:
        for item in created:
            print(f"    ✅  {item}")
    else:
        print("    (nothing new)")

    print()
    print("  Skipped :")
    if skipped:
        for item in skipped:
            print(f"    ⏭️   {item}")
    else:
        print("    (nothing skipped)")

    if errors:
        print()
        print("  Errors :")
        for err in errors:
            print(f"    ❌  {err}")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description=(
            "Initialise the chat persistence database schema and optionally "
            "insert sample seed data."
        )
    )
    parser.add_argument(
        "--seed",
        action="store_true",
        default=False,
        help="Insert sample seed data for development after verifying tables exist.",
    )
    parser.add_argument(
        "--skip-check",
        action="store_true",
        default=False,
        help="Skip the Supabase connectivity and table existence check.",
    )
    return parser.parse_args()


def main() -> int:
    """Main entry point.

    Returns:
        Exit code: 0 on success, 1 on failure.
    """
    args = parse_args()

    print()
    print(_separator("="))
    print("  CHAT PERSISTENCE DATABASE INITIALISATION")
    print(_separator("="))

    # ------------------------------------------------------------------
    # Build Supabase client
    # ------------------------------------------------------------------
    client = None
    if not args.skip_check:
        client = _build_supabase_client()
        if client is None:
            print()
            print("  ⚠️  Could not connect to Supabase.")
            print("  Set SUPABASE_URL and SUPABASE_KEY in your .env file, or")
            print("  use --skip-check to display migration SQL without connecting.")
            print()
            # Still show migration SQL even without a connection
            table_status = {t: False for t in _REQUIRED_TABLES}
            show_migration_instructions(table_status)
            return 1

    # ------------------------------------------------------------------
    # Step 1 — Check existing tables
    # ------------------------------------------------------------------
    if client is not None:
        table_status = check_prerequisites(client)
    else:
        table_status = {t: False for t in _REQUIRED_TABLES}

    # ------------------------------------------------------------------
    # Step 2 — Show migration SQL
    # ------------------------------------------------------------------
    show_migration_instructions(table_status)

    # ------------------------------------------------------------------
    # Step 3 — Health check (only if client is available)
    # ------------------------------------------------------------------
    healthy = False
    if client is not None:
        healthy = run_health_check(client)
    else:
        print()
        print("  ℹ️  Skipping health check (no Supabase connection).")

    # ------------------------------------------------------------------
    # Step 4 — Seed data (optional, only when tables are healthy)
    # ------------------------------------------------------------------
    if args.seed:
        if client is None:
            print()
            print("  ⚠️  Cannot insert seed data without a Supabase connection.")
        elif not healthy:
            print()
            print("  ⚠️  Skipping seed data — apply migrations first.")
        else:
            insert_seed_data(client)

    # ------------------------------------------------------------------
    # Final summary
    # ------------------------------------------------------------------
    _print_section("SUMMARY")

    version_map = get_migration_version(str(_MIGRATIONS_DIR))
    print("  Migration files on disk:")
    for migration_file, present in version_map.items():
        icon = "✅" if present else "❌"
        print(f"    {icon}  {migration_file}")

    print()
    if client is not None:
        if healthy:
            print("  ✅  Chat persistence database is ready.")
        else:
            print("  ❌  Chat persistence database is NOT ready.")
            print("      Apply the SQL migrations shown above, then re-run this script.")
    else:
        print("  ℹ️  No database connection — review the SQL above and apply manually.")

    print()
    print("  Next steps:")
    print("    1. Apply any missing migrations via the Supabase Dashboard SQL Editor.")
    print("    2. Re-run this script to verify all tables are accessible.")
    print("    3. Use --seed to populate sample data for local development.")
    print()

    return 0 if (client is None or healthy) else 1


if __name__ == "__main__":
    sys.exit(main())
