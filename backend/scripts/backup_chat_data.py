#!/usr/bin/env python3
"""
Backup script for chat persistence system data.

Implements:
  - Incremental daily backup (records modified since last backup)
  - Full weekly backup (all records)
  - Data integrity verification via SHA-256 checksums
  - Compressed JSON output

Usage:
    python backup_chat_data.py --mode full --output /backups/
    python backup_chat_data.py --mode incremental --since 2024-01-01T00:00:00Z
    python backup_chat_data.py --verify /backups/backup_20240101_120000.json.gz

Validates: Requirements 1.5, 8.3
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Supabase client setup
# ---------------------------------------------------------------------------

try:
    from supabase import create_client
except ImportError:
    print("ERROR: supabase package not installed. Run: pip install supabase")
    sys.exit(1)

SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")

CHAT_TABLES = [
    "conversations",
    "conversation_messages",
    "user_platform_links",
    "conversation_tags",
]

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _get_client():
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("ERROR: SUPABASE_URL and SUPABASE_KEY environment variables are required.")
        sys.exit(1)
    return create_client(SUPABASE_URL, SUPABASE_KEY)


def _fetch_table(client, table: str, since: datetime | None = None) -> list[dict]:
    """Fetch all rows from *table*, optionally filtered by *since* timestamp."""
    query = client.table(table).select("*")
    if since is not None:
        query = query.gte("created_at", since.isoformat())
    result = query.execute()
    return result.data or []


def _compute_checksum(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _write_backup(output_dir: Path, payload: dict) -> Path:
    """Write *payload* as a gzip-compressed JSON file and return the path."""
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    mode = payload.get("mode", "backup")
    filename = output_dir / f"chat_backup_{mode}_{ts}.json.gz"

    raw = json.dumps(payload, default=str, ensure_ascii=False, indent=2).encode("utf-8")
    checksum = _compute_checksum(raw)
    payload["checksum"] = checksum

    # Re-serialise with checksum included
    raw = json.dumps(payload, default=str, ensure_ascii=False, indent=2).encode("utf-8")

    with gzip.open(filename, "wb") as f:
        f.write(raw)

    return filename


# ---------------------------------------------------------------------------
# Backup modes
# ---------------------------------------------------------------------------


def run_full_backup(output_dir: Path) -> None:
    """Perform a full backup of all chat persistence tables."""
    print(f"[{datetime.now().isoformat()}] Starting FULL backup...")
    client = _get_client()

    tables_data: dict[str, list] = {}
    total_rows = 0
    for table in CHAT_TABLES:
        rows = _fetch_table(client, table)
        tables_data[table] = rows
        total_rows += len(rows)
        print(f"  {table}: {len(rows)} rows")

    payload: dict[str, Any] = {
        "mode": "full",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "total_rows": total_rows,
        "tables": tables_data,
    }

    output_dir.mkdir(parents=True, exist_ok=True)
    path = _write_backup(output_dir, payload)
    print(f"[OK] Full backup written to: {path}")
    print(f"     Total rows: {total_rows}")


def run_incremental_backup(output_dir: Path, since: datetime) -> None:
    """Perform an incremental backup of rows modified since *since*."""
    print(
        f"[{datetime.now().isoformat()}] Starting INCREMENTAL backup (since {since.isoformat()})..."
    )
    client = _get_client()

    tables_data: dict[str, list] = {}
    total_rows = 0
    for table in CHAT_TABLES:
        rows = _fetch_table(client, table, since=since)
        tables_data[table] = rows
        total_rows += len(rows)
        print(f"  {table}: {len(rows)} new/modified rows")

    payload: dict[str, Any] = {
        "mode": "incremental",
        "since": since.isoformat(),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "total_rows": total_rows,
        "tables": tables_data,
    }

    output_dir.mkdir(parents=True, exist_ok=True)
    path = _write_backup(output_dir, payload)
    print(f"[OK] Incremental backup written to: {path}")
    print(f"     Total rows: {total_rows}")


# ---------------------------------------------------------------------------
# Integrity verification
# ---------------------------------------------------------------------------


def verify_backup(backup_path: Path) -> bool:
    """Verify the integrity of a backup file using its embedded checksum."""
    print(f"Verifying: {backup_path}")
    with gzip.open(backup_path, "rb") as f:
        raw = f.read()

    data = json.loads(raw.decode("utf-8"))
    stored_checksum = data.pop("checksum", None)
    if stored_checksum is None:
        print("[FAIL] No checksum found in backup file.")
        return False

    # Recompute checksum without the checksum field
    recomputed_raw = json.dumps(data, default=str, ensure_ascii=False, indent=2).encode("utf-8")
    actual_checksum = _compute_checksum(recomputed_raw)

    if actual_checksum == stored_checksum:
        total = data.get("total_rows", "?")
        mode = data.get("mode", "?")
        created = data.get("created_at", "?")
        print(f"[OK] Checksum valid. Mode={mode}, rows={total}, created={created}")
        return True
    else:
        print(f"[FAIL] Checksum mismatch! Expected {stored_checksum}, got {actual_checksum}")
        return False


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(description="Chat persistence backup tool")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # full
    full_p = subparsers.add_parser("full", help="Full backup of all tables")
    full_p.add_argument("--output", default="./backups", help="Output directory")

    # incremental
    inc_p = subparsers.add_parser("incremental", help="Incremental backup since a timestamp")
    inc_p.add_argument("--output", default="./backups", help="Output directory")
    inc_p.add_argument(
        "--since",
        required=True,
        help="ISO-8601 timestamp (e.g. 2024-01-01T00:00:00Z)",
    )

    # verify
    ver_p = subparsers.add_parser("verify", help="Verify backup file integrity")
    ver_p.add_argument("file", help="Path to backup file (.json.gz)")

    args = parser.parse_args()

    if args.command == "full":
        run_full_backup(Path(args.output))
    elif args.command == "incremental":
        since = datetime.fromisoformat(args.since.replace("Z", "+00:00"))
        run_incremental_backup(Path(args.output), since)
    elif args.command == "verify":
        ok = verify_backup(Path(args.file))
        sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
