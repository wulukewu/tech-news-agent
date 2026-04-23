#!/usr/bin/env python3
"""
Restore script for chat persistence system data.

Implements:
  - Restore from full backup (upsert all rows)
  - Restore from incremental backup (upsert changed rows only)
  - Data integrity check before restore
  - Dry-run mode for safe preview

Usage:
    python restore_chat_data.py --file /backups/chat_backup_full_20240101.json.gz
    python restore_chat_data.py --file /backups/chat_backup_full_20240101.json.gz --dry-run
    python restore_chat_data.py --file /backups/chat_backup_incremental_20240102.json.gz

Validates: Requirements 1.5, 8.3
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import os
import sys
from pathlib import Path

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

# Restore order respects foreign-key dependencies
RESTORE_ORDER = [
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


def _compute_checksum(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _load_and_verify(backup_path: Path) -> dict:
    """Load backup file and verify its checksum. Returns parsed data."""
    print(f"Loading backup: {backup_path}")
    with gzip.open(backup_path, "rb") as f:
        raw = f.read()

    data = json.loads(raw.decode("utf-8"))
    stored_checksum = data.pop("checksum", None)

    if stored_checksum is not None:
        recomputed_raw = json.dumps(data, default=str, ensure_ascii=False, indent=2).encode("utf-8")
        actual = _compute_checksum(recomputed_raw)
        if actual != stored_checksum:
            print("[FAIL] Checksum mismatch — backup may be corrupted.")
            print(f"       Expected: {stored_checksum}")
            print(f"       Actual:   {actual}")
            sys.exit(1)
        print("[OK] Checksum verified.")
    else:
        print("[WARN] No checksum in backup file — skipping integrity check.")

    return data


def _upsert_rows(client, table: str, rows: list[dict], dry_run: bool) -> int:
    """Upsert *rows* into *table*. Returns number of rows processed."""
    if not rows:
        return 0
    if dry_run:
        print(f"  [DRY-RUN] Would upsert {len(rows)} rows into {table}")
        return len(rows)

    # Upsert in batches of 500 to avoid request size limits
    batch_size = 500
    total = 0
    for i in range(0, len(rows), batch_size):
        batch = rows[i : i + batch_size]
        client.table(table).upsert(batch).execute()
        total += len(batch)

    return total


# ---------------------------------------------------------------------------
# Restore
# ---------------------------------------------------------------------------


def run_restore(backup_path: Path, dry_run: bool = False) -> None:
    """Restore data from a backup file."""
    data = _load_and_verify(backup_path)

    mode = data.get("mode", "unknown")
    created_at = data.get("created_at", "unknown")
    total_rows = data.get("total_rows", 0)
    tables_data: dict = data.get("tables", {})

    print("\nBackup info:")
    print(f"  Mode:       {mode}")
    print(f"  Created at: {created_at}")
    print(f"  Total rows: {total_rows}")
    if dry_run:
        print("  [DRY-RUN MODE — no changes will be made]\n")

    client = None if dry_run else _get_client()

    restored = 0
    for table in RESTORE_ORDER:
        rows = tables_data.get(table, [])
        if not rows:
            print(f"  {table}: 0 rows (skipped)")
            continue
        count = _upsert_rows(client, table, rows, dry_run)
        restored += count
        print(f"  {table}: {count} rows {'(would restore)' if dry_run else 'restored'}")

    print(f"\n[OK] Restore {'preview' if dry_run else 'complete'}. Rows: {restored}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(description="Chat persistence restore tool")
    parser.add_argument("--file", required=True, help="Path to backup file (.json.gz)")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview restore without writing to database",
    )
    args = parser.parse_args()

    run_restore(Path(args.file), dry_run=args.dry_run)


if __name__ == "__main__":
    main()
