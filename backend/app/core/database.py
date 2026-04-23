"""
Chat Persistence Database Models and Health Checks

This module provides Pydantic models representing the chat persistence tables
and utility functions for database health verification and migration tracking.

The project uses Supabase (not direct SQLAlchemy connections), so all models
are Pydantic-based data classes that mirror the table schemas. Database
operations are performed via the Supabase client using the
``client.table("tablename").select(...)`` pattern.

Validates: Requirements 7.1, 8.5
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, Field

from app.core.logger import get_logger

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Migration file registry
# ---------------------------------------------------------------------------

#: Ordered list of SQL migration files that belong to the chat persistence
#: system.  The init script uses this list to determine which migrations have
#: already been applied and which still need to be run.
MIGRATION_FILES: list[str] = [
    "001_chat_persistence.sql",
    "002_chat_persistence_indexes.sql",
]


# ---------------------------------------------------------------------------
# Pydantic models — mirror the database table schemas
# ---------------------------------------------------------------------------


class Conversation(BaseModel):
    """Represents a row in the ``conversations`` table.

    The ``conversations`` table stores the top-level metadata for each
    conversation thread.  Individual messages are stored in the separate
    ``conversation_messages`` table.
    """

    id: UUID
    user_id: UUID
    title: str = "Untitled Conversation"
    summary: Optional[str] = None
    platform: str = "web"
    tags: list[str] = Field(default_factory=list)
    is_archived: bool = False
    is_favorite: bool = False
    created_at: datetime
    last_message_at: datetime
    message_count: int = 0
    metadata: dict[str, Any] = Field(default_factory=dict)

    class Config:
        from_attributes = True


class ConversationMessage(BaseModel):
    """Represents a row in the ``conversation_messages`` table.

    Each row stores a single message within a conversation, including the
    role of the author (``user`` or ``assistant``), the platform it was sent
    from, and any platform-specific metadata.
    """

    id: UUID
    conversation_id: UUID
    role: str  # 'user' | 'assistant'
    content: str
    platform: str = "web"
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime

    class Config:
        from_attributes = True


class UserPlatformLink(BaseModel):
    """Represents a row in the ``user_platform_links`` table.

    Links a system user account to their identity on an external platform
    (e.g. Discord).  A single ``user_id`` can have links to multiple
    platforms.
    """

    user_id: UUID
    platform: str  # 'web' | 'discord'
    platform_user_id: str
    platform_username: Optional[str] = None
    linked_at: datetime
    is_active: bool = True
    verification_data: dict[str, Any] = Field(default_factory=dict)

    class Config:
        from_attributes = True


class ConversationTag(BaseModel):
    """Represents a row in the ``conversation_tags`` table.

    Manages the tag vocabulary per user, including an optional display colour
    and a denormalised usage counter for fast sorting.
    """

    id: UUID
    user_id: UUID
    tag_name: str
    color: Optional[str] = None  # hex colour code, e.g. '#3B82F6'
    created_at: datetime
    usage_count: int = 0

    class Config:
        from_attributes = True


# ---------------------------------------------------------------------------
# Health check data structures
# ---------------------------------------------------------------------------


@dataclass
class TableHealthResult:
    """Health check result for a single database table."""

    table_name: str
    accessible: bool
    error: Optional[str] = None
    row_count: Optional[int] = None


@dataclass
class ChatDatabaseHealth:
    """Aggregated health check results for all chat persistence tables.

    Attributes:
        healthy: ``True`` when every required table is accessible.
        tables: Per-table health results keyed by table name.
        checked_at: UTC timestamp of when the check was performed.
        errors: List of error messages collected during the check.
    """

    healthy: bool
    tables: dict[str, TableHealthResult] = field(default_factory=dict)
    checked_at: datetime = field(default_factory=datetime.utcnow)
    errors: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Health check function
# ---------------------------------------------------------------------------

#: Tables that must be accessible for the chat persistence system to be
#: considered healthy.
_REQUIRED_TABLES: list[str] = [
    "conversations",
    "conversation_messages",
    "user_platform_links",
    "conversation_tags",
]


async def check_chat_tables_health(client: Any) -> ChatDatabaseHealth:
    """Verify that all chat persistence tables exist and are accessible.

    Performs a lightweight ``SELECT`` (limit 0) against each required table
    using the Supabase client.  This confirms that the table exists and that
    the current credentials have read access, without fetching any actual
    rows.

    Args:
        client: An initialised Supabase ``Client`` instance.

    Returns:
        A :class:`ChatDatabaseHealth` dataclass summarising the result of
        each table check.  ``healthy`` is ``True`` only when *all* required
        tables are accessible.

    Example::

        from supabase import create_client
        from app.core.database import check_chat_tables_health

        client = create_client(url, key)
        health = await check_chat_tables_health(client)
        if not health.healthy:
            print(health.errors)
    """
    logger.info("Running chat database health check", tables=_REQUIRED_TABLES)

    table_results: dict[str, TableHealthResult] = {}
    errors: list[str] = []

    for table_name in _REQUIRED_TABLES:
        result = _check_single_table(client, table_name)
        table_results[table_name] = result
        if not result.accessible:
            error_msg = f"Table '{table_name}' is not accessible: {result.error}"
            errors.append(error_msg)
            logger.warning("Table health check failed", table=table_name, error=result.error)
        else:
            logger.info("Table health check passed", table=table_name)

    overall_healthy = len(errors) == 0

    health = ChatDatabaseHealth(
        healthy=overall_healthy,
        tables=table_results,
        checked_at=datetime.utcnow(),
        errors=errors,
    )

    if overall_healthy:
        logger.info("Chat database health check passed — all tables accessible")
    else:
        logger.warning(
            "Chat database health check failed",
            failed_tables=[t for t, r in table_results.items() if not r.accessible],
        )

    return health


def _check_single_table(client: Any, table_name: str) -> TableHealthResult:
    """Perform a lightweight accessibility check on a single table.

    Args:
        client: An initialised Supabase ``Client`` instance.
        table_name: Name of the table to check.

    Returns:
        A :class:`TableHealthResult` with the outcome of the check.
    """
    try:
        response = client.table(table_name).select("*", count="exact").limit(0).execute()
        row_count = response.count if hasattr(response, "count") else None
        return TableHealthResult(
            table_name=table_name,
            accessible=True,
            row_count=row_count,
        )
    except Exception as exc:
        return TableHealthResult(
            table_name=table_name,
            accessible=False,
            error=str(exc),
        )


# ---------------------------------------------------------------------------
# Migration version tracking
# ---------------------------------------------------------------------------


def get_migration_version(migrations_dir: Optional[str] = None) -> dict[str, bool]:
    """Check which chat persistence migration files are present on disk.

    This function does *not* query the database — it simply inspects the
    ``backend/scripts/migrations/`` directory to determine which SQL files
    from :data:`MIGRATION_FILES` exist locally.  The init script uses this
    information to decide which migrations still need to be applied.

    Args:
        migrations_dir: Optional path to the migrations directory.  Defaults
            to ``backend/scripts/migrations/`` relative to this file.

    Returns:
        A dictionary mapping each migration filename to a boolean indicating
        whether the file exists on disk.

    Example::

        versions = get_migration_version()
        # {'001_chat_persistence.sql': True, '002_chat_persistence_indexes.sql': True}
    """
    import os
    from pathlib import Path

    if migrations_dir is None:
        # Resolve relative to this file: backend/app/core/database.py
        # → backend/scripts/migrations/
        this_file = Path(__file__).resolve()
        migrations_dir = str(this_file.parent.parent.parent / "scripts" / "migrations")

    version_map: dict[str, bool] = {}
    for migration_file in MIGRATION_FILES:
        full_path = os.path.join(migrations_dir, migration_file)
        version_map[migration_file] = os.path.isfile(full_path)
        logger.info(
            "Migration file check",
            file=migration_file,
            present=version_map[migration_file],
            path=full_path,
        )

    return version_map
