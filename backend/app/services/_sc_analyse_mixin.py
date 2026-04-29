"""Mixin extracted from smart_conversation.py."""
from __future__ import annotations

from collections import Counter
from datetime import datetime, timedelta, timezone
from uuid import UUID

from app.core.errors import ExternalServiceError
from app.core.logger import get_logger
from app.repositories.conversation import ConversationFilters

logger = get_logger(__name__)


class AnalyseMixin:
    async def analyse_conversations(
        self,
        user_id: UUID | str,
        *,
        days: int = 30,
        max_conversations: int = 100,
    ) -> ConversationInsights:
        """Analyse a user's conversation history and generate insights.

        Fetches recent conversations and their messages, then:
        - Computes topic distribution from tags and titles.
        - Calculates activity metrics (active days, messages/day).
        - Identifies interest areas and potential knowledge gaps.
        - Calls the LLM to generate personalised learning suggestions and a
          trend summary.

        Args:
            user_id: UUID of the user to analyse.
            days: Look-back window in days. Defaults to 30.
            max_conversations: Maximum number of conversations to include in
                the analysis. Defaults to 100.

        Returns:
            A :class:`ConversationInsights` dataclass with all computed
            metrics and LLM-generated suggestions.

        Raises:
            DatabaseError: If the database operations fail.

        Validates: Requirements 6.1, 6.3, 6.4, 6.5
        """
        self.logger.info(
            "Analysing conversations",
            user_id=str(user_id),
            days=days,
        )

        # Fetch recent conversations
        conversations = await self.conversation_repo.list_conversations(
            user_id=user_id,
            filters=ConversationFilters(
                is_archived=False,
                limit=max_conversations,
                order_by="last_message_at",
                ascending=False,
            ),
        )

        if not conversations:
            self.logger.info("No conversations found for analysis", user_id=str(user_id))
            return ConversationInsights()

        # Filter to the look-back window
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        recent = [c for c in conversations if c.last_message_at >= cutoff]

        if not recent:
            recent = conversations[:10]  # Fall back to most recent 10

        # ---- Activity metrics ----------------------------------------
        active_day_set: set[str] = set()
        total_messages = 0
        for conv in recent:
            active_day_set.add(conv.last_message_at.strftime("%Y-%m-%d"))
            total_messages += conv.message_count

        active_days = len(active_day_set)
        avg_messages_per_day = round(total_messages / max(active_days, 1), 2)

        # ---- Topic / tag distribution --------------------------------
        tag_counter: Counter[str] = Counter()
        for conv in recent:
            for tag in conv.tags or []:
                tag_counter[tag] += 1

        topic_distribution = dict(tag_counter.most_common(20))
        top_tags = [tag for tag, _ in tag_counter.most_common(10)]

        # ---- Interest areas from titles ------------------------------
        title_text = " ".join(c.title for c in recent)
        interest_keywords = _extract_keywords(title_text, top_n=15)
        interest_areas = list(interest_keywords)[:10]

        # ---- LLM-powered insights ------------------------------------
        # Build a compact context for the LLM
        context_lines: list[str] = []
        for conv in recent[:20]:  # Limit to 20 for prompt size
            tags_str = ", ".join(conv.tags) if conv.tags else "none"
            context_lines.append(f"- {conv.title} [tags: {tags_str}]")

        context_text = "\n".join(context_lines)
        tag_summary = ", ".join(f"{t}({n})" for t, n in tag_counter.most_common(8))

        system_prompt = (
            "You are a learning analytics assistant.\n"
            "Given a user's recent conversation history, produce a JSON object with:\n"
            '  "knowledge_gaps": list of 2-3 topics the user seems to struggle with '
            "or has incomplete understanding of (inferred from conversation titles).\n"
            '  "learning_suggestions": list of 3-5 specific, actionable next steps '
            "the user should take to deepen their knowledge.\n"
            '  "trend_summary": a 2-3 sentence paragraph describing the user\'s '
            "learning trends and focus areas.\n\n"
            "Use the same language as the conversation titles (Chinese or English).\n"
            "Return ONLY valid JSON — no markdown fences."
        )
        user_prompt = (
            f"Recent conversations ({len(recent)} total, last {days} days):\n"
            f"{context_text}\n\n"
            f"Top tags: {tag_summary}\n"
            f"Active days: {active_days}, avg messages/day: {avg_messages_per_day}"
        )

        knowledge_gaps: list[str] = []
        learning_suggestions: list[str] = []
        trend_summary = ""

        try:
            raw = await self._call_llm_text(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                model=_SMART_MODEL,
                max_tokens=600,
                context=f"analyse_conversations({user_id})",
            )
            parsed = _safe_parse_json(raw)
            knowledge_gaps = parsed.get("knowledge_gaps") or []
            learning_suggestions = parsed.get("learning_suggestions") or []
            trend_summary = parsed.get("trend_summary") or ""
        except ExternalServiceError:
            self.logger.warning(
                "LLM call failed for conversation analysis — returning partial insights",
                user_id=str(user_id),
            )

        insights = ConversationInsights(
            topic_distribution=topic_distribution,
            active_days=active_days,
            avg_messages_per_day=avg_messages_per_day,
            top_tags=top_tags,
            knowledge_gaps=knowledge_gaps,
            interest_areas=interest_areas,
            learning_suggestions=learning_suggestions,
            trend_summary=trend_summary,
        )

        self.logger.info(
            "Conversation analysis complete",
            user_id=str(user_id),
            active_days=active_days,
            conversations_analysed=len(recent),
        )
        return insights

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------
