"""
Preference Model

Manages per-user category weights and learning settings in the database.
Requirements: 4.3, 4.4, 4.5, 12.1, 12.2
"""

import json
import logging
from datetime import UTC, datetime
from typing import Any

from app.services.supabase_service import SupabaseService

logger = logging.getLogger(__name__)

DEFAULT_WEIGHT = 0.5
MIN_WEIGHT = 0.05
MAX_WEIGHT = 1.0


class PreferenceModel:
    """Reads and updates user preference weights."""

    def __init__(self, supabase: SupabaseService | None = None):
        self.supabase = supabase or SupabaseService()

    async def get(self, user_id: str) -> dict[str, Any]:
        """Return the full preference model row for a user (creates default if missing)."""
        try:
            resp = (
                self.supabase.client.table("preference_model")
                .select("*")
                .eq("user_id", user_id)
                .single()
                .execute()
            )
            if resp.data:
                row = resp.data
                if isinstance(row.get("category_weights"), str):
                    row["category_weights"] = json.loads(row["category_weights"])
                return row
        except Exception:
            pass
        # Create default
        return await self._create_default(user_id)

    async def apply_adjustments(
        self, user_id: str, adjustments: dict[str, float]
    ) -> dict[str, float]:
        """
        Apply weight_adjustments from FeedbackProcessor to stored weights.

        Uses gradual adjustment: new_weight = old + delta * 0.3 (dampening).
        Returns updated weights dict.
        """
        model = await self.get(user_id)
        weights: dict[str, float] = model.get("category_weights") or {}

        for topic, delta in adjustments.items():
            current = weights.get(topic, DEFAULT_WEIGHT)
            # Gradual adjustment with dampening
            new_weight = current + delta * 0.3
            weights[topic] = round(max(MIN_WEIGHT, min(MAX_WEIGHT, new_weight)), 3)

        await self._save_weights(user_id, weights)
        return weights

    async def set_weights(self, user_id: str, weights: dict[str, float]) -> None:
        """Directly set category weights (for manual override)."""
        # Clamp all values
        clamped = {k: round(max(MIN_WEIGHT, min(MAX_WEIGHT, v)), 3) for k, v in weights.items()}
        await self._save_weights(user_id, clamped)

    async def update_settings(self, user_id: str, settings: dict[str, Any]) -> None:
        """Update learning settings (enabled, max_weekly_conversations)."""
        allowed = {"learning_enabled", "max_weekly_conversations"}
        update = {k: v for k, v in settings.items() if k in allowed}
        if not update:
            return
        update["updated_at"] = datetime.now(UTC).isoformat()
        try:
            self.supabase.client.table("preference_model").update(update).eq(
                "user_id", user_id
            ).execute()
        except Exception as exc:
            logger.error("Failed to update settings: %s", exc)

    # ── private ──────────────────────────────────────────────────────────────

    async def _save_weights(self, user_id: str, weights: dict[str, float]) -> None:
        try:
            self.supabase.client.table("preference_model").upsert(
                {
                    "user_id": user_id,
                    "category_weights": json.dumps(weights),
                    "updated_at": datetime.now(UTC).isoformat(),
                }
            ).execute()
        except Exception as exc:
            logger.error("Failed to save preference weights: %s", exc)

    async def _create_default(self, user_id: str) -> dict[str, Any]:
        default = {
            "user_id": user_id,
            "category_weights": "{}",
            "learning_enabled": True,
            "max_weekly_conversations": 3,
            "conversations_this_week": 0,
            "week_reset_at": datetime.now(UTC).isoformat(),
        }
        try:
            self.supabase.client.table("preference_model").upsert(default).execute()
        except Exception as exc:
            logger.warning("Could not create default preference model: %s", exc)
        default["category_weights"] = {}
        return default
