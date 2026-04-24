"""
Conversation Manager

Generates personalized learning questions and manages conversation lifecycle.
Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 7.1, 7.2, 7.3, 7.4, 7.5
"""

import json
import logging
from datetime import UTC, datetime
from typing import Any

from openai import AsyncOpenAI

from app.core.config import settings
from app.services.supabase_service import SupabaseService

logger = logging.getLogger(__name__)

CONV_MODEL = "llama-3.1-8b-instant"

SYSTEM_PROMPT = """You are a personalized learning assistant for a tech news reader.
Generate a concise, friendly question to understand the user's reading preferences.
Return ONLY valid JSON:
{
  "question": "...",
  "options": ["option1", "option2", "option3", null]
}
options can be null for open-ended questions. Keep question under 100 chars."""


class ConversationManager:
    """Creates and manages proactive learning conversations."""

    def __init__(self, supabase: SupabaseService | None = None):
        self.supabase = supabase or SupabaseService()
        self.llm = AsyncOpenAI(
            base_url="https://api.groq.com/openai/v1",
            api_key=settings.groq_api_key,
            timeout=30,
        )

    async def create_conversation(self, user_id: str, context: dict[str, Any]) -> dict[str, Any]:
        """
        Generate and persist a new learning conversation for the user.

        Args:
            user_id: Target user.
            context: Trigger context (reason, anomalies, new_interests, etc.)

        Returns:
            The created conversation row dict.
        """
        reason = context.get("reason", "general")
        conv_type = self._reason_to_type(reason)
        prompt = self._build_prompt(reason, context)

        question, options = await self._generate_question(prompt)

        row = {
            "user_id": user_id,
            "conversation_type": conv_type,
            "question": question,
            "options": json.dumps(options) if options else None,
            "status": "pending",
            "context_data": json.dumps(context),
        }
        try:
            resp = self.supabase.client.table("learning_conversations").insert(row).execute()
            created = (resp.data or [{}])[0]
            if created.get("options") and isinstance(created["options"], str):
                created["options"] = json.loads(created["options"])
            return created
        except Exception as exc:
            logger.error("Failed to create conversation: %s", exc)
            return {**row, "id": None}

    async def get_pending_conversations(self, user_id: str) -> list[dict[str, Any]]:
        """Return all pending (unanswered) conversations for a user."""
        try:
            resp = (
                self.supabase.client.table("learning_conversations")
                .select("*")
                .eq("user_id", user_id)
                .eq("status", "pending")
                .order("created_at", desc=False)
                .execute()
            )
            rows = resp.data or []
            for r in rows:
                if r.get("options") and isinstance(r["options"], str):
                    r["options"] = json.loads(r["options"])
                if r.get("context_data") and isinstance(r["context_data"], str):
                    r["context_data"] = json.loads(r["context_data"])
            return rows
        except Exception as exc:
            logger.warning("Failed to fetch pending conversations: %s", exc)
            return []

    async def mark_answered(self, conversation_id: str, response: str) -> dict[str, Any]:
        """Record user response and mark conversation as answered."""
        try:
            resp = (
                self.supabase.client.table("learning_conversations")
                .update(
                    {
                        "response": response,
                        "status": "answered",
                        "responded_at": datetime.now(UTC).isoformat(),
                    }
                )
                .eq("id", conversation_id)
                .execute()
            )
            return (resp.data or [{}])[0]
        except Exception as exc:
            logger.error("Failed to mark conversation answered: %s", exc)
            return {}

    # ── helpers ──────────────────────────────────────────────────────────────

    def _reason_to_type(self, reason: str) -> str:
        return {
            "engagement_drop": "preference_adjust",
            "new_interest": "interest_confirm",
            "interest_decay": "preference_adjust",
        }.get(reason, "feedback")

    def _build_prompt(self, reason: str, context: dict[str, Any]) -> str:
        if reason == "engagement_drop":
            cats = [a["category"] for a in context.get("anomalies", [])]
            return f"User's engagement dropped significantly in: {', '.join(cats)}. Ask why."
        if reason == "new_interest":
            cats = context.get("new_interests", [])
            return f"User recently explored new topics: {', '.join(cats)}. Confirm interest."
        if reason == "interest_decay":
            cats = context.get("decaying_interests", [])
            return f"User stopped reading about: {', '.join(cats)}. Ask if still interested."
        return "Ask the user about their current reading preferences."

    async def _generate_question(self, prompt: str) -> tuple[str, list[str] | None]:
        try:
            resp = await self.llm.chat.completions.create(
                model=CONV_MODEL,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                max_tokens=150,
                temperature=0.7,
            )
            raw = resp.choices[0].message.content or "{}"
            raw = raw.strip()
            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]
            data = json.loads(raw)
            return data.get("question", prompt), data.get("options")
        except Exception as exc:
            logger.warning("LLM question generation failed: %s", exc)
            return prompt, None
