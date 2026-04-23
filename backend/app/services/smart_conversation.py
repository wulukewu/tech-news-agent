"""
Smart Conversation Service

Provides intelligent features on top of the core conversation persistence
system:

  7.1  Auto title generation  — derives a concise, meaningful title from the
       first few messages of a conversation using the LLM.

  7.2  Conversation summary generation  — produces a short summary and
       extracts key insights from a full conversation thread.

  7.3  Related conversation recommendation  — finds conversations that are
       topically similar to a given conversation based on keyword overlap and
       tag matching.

  7.4  Conversation analysis and insights  — analyses a user's conversation
       history to surface topic distribution, activity trends, knowledge gaps,
       and personalised learning suggestions.

All LLM calls use the Groq-backed ``LLMService`` client and follow the same
retry / rate-limit patterns established elsewhere in the codebase.

Validates: Requirements 3.2, 3.5, 6.1, 6.2, 6.3, 6.4, 6.5
"""

from __future__ import annotations

import asyncio
import json
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Optional
from uuid import UUID

from openai import AsyncOpenAI

from app.core.config import settings
from app.core.errors import DatabaseError, ErrorCode, ExternalServiceError
from app.core.logger import get_logger
from app.repositories.conversation import ConversationFilters, ConversationRepository
from app.repositories.message import MessageRepository

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# LLM model constants (mirrors llm_service.py)
# ---------------------------------------------------------------------------

_FAST_MODEL = "llama-3.1-8b-instant"
_SMART_MODEL = "llama-3.3-70b-versatile"
_API_TIMEOUT = 30  # seconds
_MAX_RETRIES = 2
_RETRY_DELAYS = [2, 4]  # seconds

# ---------------------------------------------------------------------------
# Result data-classes
# ---------------------------------------------------------------------------


@dataclass
class ConversationInsights:
    """Structured output from the conversation analysis service (7.4).

    Attributes:
        topic_distribution: Mapping of topic label → message count.
        active_days: Number of distinct calendar days with activity.
        avg_messages_per_day: Average messages sent per active day.
        top_tags: Most-used tags across all conversations.
        knowledge_gaps: Topics the user has asked about but received
            incomplete answers for (heuristic).
        interest_areas: Topics the user engages with most frequently.
        learning_suggestions: Personalised next-step recommendations.
        trend_summary: Human-readable paragraph describing trends.
        generated_at: UTC timestamp of when the analysis was run.
    """

    topic_distribution: dict[str, int] = field(default_factory=dict)
    active_days: int = 0
    avg_messages_per_day: float = 0.0
    top_tags: list[str] = field(default_factory=list)
    knowledge_gaps: list[str] = field(default_factory=list)
    interest_areas: list[str] = field(default_factory=list)
    learning_suggestions: list[str] = field(default_factory=list)
    trend_summary: str = ""
    generated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class RelatedConversation:
    """A single related-conversation recommendation result.

    Attributes:
        conversation_id: UUID of the recommended conversation.
        title: Title of the recommended conversation.
        similarity_score: Normalised score in [0, 1] (higher = more similar).
        shared_tags: Tags that appear in both conversations.
        reason: Short human-readable explanation of why it was recommended.
    """

    conversation_id: UUID
    title: str
    similarity_score: float
    shared_tags: list[str] = field(default_factory=list)
    reason: str = ""


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------


class SmartConversationService:
    """Intelligent conversation features built on top of the persistence layer.

    Inject this service wherever smart conversation capabilities are needed.
    It depends on:
    - ``ConversationRepository`` for conversation metadata access.
    - ``MessageRepository`` for message content access.
    - An ``AsyncOpenAI`` client pointed at the Groq API for LLM calls.

    All public methods are ``async``.

    Validates: Requirements 3.2, 3.5, 6.1, 6.2, 6.3, 6.4, 6.5
    """

    def __init__(
        self,
        conversation_repo: ConversationRepository,
        message_repo: MessageRepository,
        llm_client: Optional[AsyncOpenAI] = None,
    ) -> None:
        """Initialise the service.

        Args:
            conversation_repo: Repository for conversation data access.
            message_repo: Repository for message data access.
            llm_client: Optional pre-built ``AsyncOpenAI`` client.  When
                omitted a new client is created using ``settings.groq_api_key``.
        """
        self.conversation_repo = conversation_repo
        self.message_repo = message_repo
        self.llm = llm_client or AsyncOpenAI(
            base_url="https://api.groq.com/openai/v1",
            api_key=settings.groq_api_key,
            timeout=_API_TIMEOUT,
        )
        self.logger = get_logger(f"{__name__}.SmartConversationService")

    # ------------------------------------------------------------------
    # 7.1  Auto title generation
    # ------------------------------------------------------------------

    async def generate_title(
        self,
        conversation_id: UUID | str,
        user_id: UUID | str,
        *,
        max_messages: int = 6,
        persist: bool = True,
    ) -> str:
        """Generate a concise title for a conversation from its first messages.

        Fetches up to ``max_messages`` messages (oldest-first) and asks the
        LLM to produce a short, descriptive title in the same language as the
        conversation.  If ``persist`` is ``True`` the generated title is
        written back to the database.

        Args:
            conversation_id: UUID of the conversation.
            user_id: UUID of the owning user.
            max_messages: Number of messages to sample for title generation.
                Defaults to 6.
            persist: When ``True`` (default) the title is saved to the DB.

        Returns:
            The generated title string.

        Raises:
            ExternalServiceError: If the LLM call fails after all retries.
            DatabaseError: If the database operations fail.

        Validates: Requirement 3.2
        """
        self.logger.info(
            "Generating title",
            conversation_id=str(conversation_id),
            user_id=str(user_id),
        )

        # Fetch the first few messages (ascending = oldest first)
        messages = await self.message_repo.get_messages(
            conversation_id,
            limit=max_messages,
            ascending=True,
        )

        if not messages:
            self.logger.warning(
                "No messages found for title generation",
                conversation_id=str(conversation_id),
            )
            return "New Conversation"

        # Build a compact transcript for the prompt
        transcript = _build_transcript(messages, max_chars=1200)

        system_prompt = (
            "You are a helpful assistant that creates concise conversation titles.\n"
            "Given the beginning of a conversation, produce a short title (5–10 words) "
            "that captures the main topic.\n"
            "Rules:\n"
            "- Use the same language as the conversation (Chinese or English).\n"
            "- Do NOT use quotation marks or punctuation at the end.\n"
            "- Return ONLY the title text, nothing else."
        )
        user_prompt = f"Conversation:\n{transcript}\n\nTitle:"

        title = await self._call_llm_text(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            model=_FAST_MODEL,
            max_tokens=30,
            context=f"generate_title({conversation_id})",
        )

        # Sanitise: strip quotes, newlines, leading/trailing whitespace
        title = title.strip().strip("\"'").strip()
        if not title:
            title = "New Conversation"

        if persist:
            try:
                await self.conversation_repo.update_title(
                    conversation_id=conversation_id,
                    user_id=user_id,
                    title=title,
                )
                self.logger.info(
                    "Title persisted",
                    conversation_id=str(conversation_id),
                    title=title,
                )
            except DatabaseError:
                # Non-fatal: log and return the generated title anyway
                self.logger.warning(
                    "Failed to persist generated title (non-fatal)",
                    conversation_id=str(conversation_id),
                )

        return title

    # ------------------------------------------------------------------
    # 7.2  Conversation summary generation
    # ------------------------------------------------------------------

    async def generate_summary(
        self,
        conversation_id: UUID | str,
        user_id: UUID | str,
        *,
        max_messages: int = 40,
        persist: bool = True,
    ) -> str:
        """Generate a summary and key insights for a conversation.

        Fetches up to ``max_messages`` messages and asks the LLM to produce
        a concise summary (≤ 200 words) plus 2–3 key insights.  When
        ``persist`` is ``True`` the summary is written back to the
        ``conversations.summary`` column.

        Args:
            conversation_id: UUID of the conversation.
            user_id: UUID of the owning user.
            max_messages: Maximum number of messages to include in the
                context window.  Defaults to 40.
            persist: When ``True`` (default) the summary is saved to the DB.

        Returns:
            The generated summary string.

        Raises:
            ExternalServiceError: If the LLM call fails after all retries.
            DatabaseError: If the database operations fail.

        Validates: Requirement 6.2
        """
        self.logger.info(
            "Generating summary",
            conversation_id=str(conversation_id),
            user_id=str(user_id),
        )

        messages = await self.message_repo.get_messages(
            conversation_id,
            limit=max_messages,
            ascending=True,
        )

        if not messages:
            self.logger.warning(
                "No messages found for summary generation",
                conversation_id=str(conversation_id),
            )
            return ""

        transcript = _build_transcript(messages, max_chars=3000)

        system_prompt = (
            "You are a helpful assistant that summarises conversations.\n"
            "Given a conversation transcript, produce:\n"
            "1. A concise summary (≤ 150 words) of what was discussed.\n"
            "2. 2–3 key insights or takeaways, each on its own line prefixed with '• '.\n\n"
            "Use the same language as the conversation (Chinese or English).\n"
            "Return ONLY the summary and insights — no extra commentary."
        )
        user_prompt = f"Conversation:\n{transcript}"

        summary = await self._call_llm_text(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            model=_SMART_MODEL,
            max_tokens=400,
            context=f"generate_summary({conversation_id})",
        )

        summary = summary.strip()

        if persist and summary:
            try:
                await self.conversation_repo.update_conversation(
                    conversation_id=conversation_id,
                    user_id=user_id,
                    updates={"summary": summary},
                )
                self.logger.info(
                    "Summary persisted",
                    conversation_id=str(conversation_id),
                )
            except DatabaseError:
                self.logger.warning(
                    "Failed to persist generated summary (non-fatal)",
                    conversation_id=str(conversation_id),
                )

        return summary

    # ------------------------------------------------------------------
    # 7.3  Related conversation recommendation
    # ------------------------------------------------------------------

    async def get_related_conversations(
        self,
        conversation_id: UUID | str,
        user_id: UUID | str,
        *,
        limit: int = 5,
    ) -> list[RelatedConversation]:
        """Find conversations related to the given one.

        Uses a lightweight keyword + tag overlap heuristic:
        1. Fetch the target conversation's title, tags, and first-message
           content.
        2. Fetch the user's recent non-archived conversations (up to 50).
        3. Score each candidate by tag overlap and keyword overlap in titles.
        4. Return the top ``limit`` results (excluding the target itself).

        This approach is intentionally fast and does not require a vector
        store, making it suitable for real-time use.

        Args:
            conversation_id: UUID of the reference conversation.
            user_id: UUID of the owning user.
            limit: Maximum number of recommendations to return. Defaults to 5.

        Returns:
            List of :class:`RelatedConversation` objects sorted by
            ``similarity_score`` descending.

        Raises:
            DatabaseError: If the database operations fail.

        Validates: Requirements 3.5, 6.4
        """
        self.logger.info(
            "Finding related conversations",
            conversation_id=str(conversation_id),
            user_id=str(user_id),
            limit=limit,
        )

        # Fetch the reference conversation
        reference = await self.conversation_repo.get_conversation(
            conversation_id=conversation_id,
            user_id=user_id,
        )
        if reference is None:
            self.logger.warning(
                "Reference conversation not found",
                conversation_id=str(conversation_id),
            )
            return []

        # Fetch a sample of the reference conversation's messages for keywords
        ref_messages = await self.message_repo.get_messages(
            conversation_id,
            limit=10,
            ascending=True,
        )
        ref_keywords = _extract_keywords(
            " ".join([reference.title] + [m.content for m in ref_messages])
        )
        ref_tags = set(reference.tags or [])

        # Fetch candidate conversations (recent, non-archived)
        candidates = await self.conversation_repo.list_conversations(
            user_id=user_id,
            filters=ConversationFilters(
                is_archived=False,
                limit=50,
                order_by="last_message_at",
                ascending=False,
            ),
        )

        results: list[RelatedConversation] = []
        for candidate in candidates:
            # Skip the reference conversation itself
            if str(candidate.id) == str(conversation_id):
                continue

            cand_tags = set(candidate.tags or [])
            shared_tags = list(ref_tags & cand_tags)

            cand_keywords = _extract_keywords(candidate.title)
            keyword_overlap = len(ref_keywords & cand_keywords)

            # Normalised score: tag overlap weighted 0.6, keyword overlap 0.4
            tag_score = len(shared_tags) / max(len(ref_tags | cand_tags), 1)
            kw_score = keyword_overlap / max(len(ref_keywords | cand_keywords), 1)
            score = round(0.6 * tag_score + 0.4 * kw_score, 4)

            if score > 0:
                reason = _build_recommendation_reason(shared_tags, keyword_overlap)
                results.append(
                    RelatedConversation(
                        conversation_id=candidate.id,
                        title=candidate.title,
                        similarity_score=score,
                        shared_tags=shared_tags,
                        reason=reason,
                    )
                )

        # Sort by score descending and return top-N
        results.sort(key=lambda r: r.similarity_score, reverse=True)
        top = results[:limit]

        self.logger.info(
            "Related conversations found",
            conversation_id=str(conversation_id),
            count=len(top),
        )
        return top

    # ------------------------------------------------------------------
    # 7.4  Conversation analysis and insights
    # ------------------------------------------------------------------

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

    async def _call_llm_text(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        model: str,
        max_tokens: int,
        context: str,
    ) -> str:
        """Call the Groq LLM and return the response text.

        Implements the same retry-with-exponential-backoff pattern used in
        ``LLMService._call_api_with_retry``.

        Args:
            system_prompt: System message content.
            user_prompt: User message content.
            model: Groq model identifier.
            max_tokens: Maximum tokens in the response.
            context: Human-readable description for logging.

        Returns:
            Stripped response text from the LLM.

        Raises:
            ExternalServiceError: If all retry attempts fail.
        """
        last_exc: Optional[Exception] = None

        for attempt in range(_MAX_RETRIES + 1):
            try:
                if attempt > 0:
                    self.logger.info(
                        "LLM retry",
                        attempt=attempt,
                        max_retries=_MAX_RETRIES,
                        context=context,
                    )

                response = await self.llm.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    temperature=0.4,
                    max_tokens=max_tokens,
                )

                content = response.choices[0].message.content or ""
                return content.strip()

            except Exception as exc:
                last_exc = exc

                if attempt >= _MAX_RETRIES:
                    self.logger.error(
                        "LLM call failed after all retries",
                        context=context,
                        error=str(exc),
                        exc_info=True,
                    )
                    raise ExternalServiceError(
                        f"LLM call failed for {context}: {exc}",
                        error_code=ErrorCode.EXTERNAL_LLM_ERROR,
                        original_error=exc,
                    ) from exc

                # Respect Retry-After header if present
                delay = _RETRY_DELAYS[attempt]
                if hasattr(exc, "response") and hasattr(exc.response, "headers"):
                    retry_after = exc.response.headers.get("Retry-After")
                    if retry_after:
                        try:
                            delay = float(retry_after)
                        except (ValueError, TypeError):
                            pass

                self.logger.warning(
                    "LLM call failed, retrying",
                    context=context,
                    attempt=attempt + 1,
                    delay=delay,
                    error=str(exc),
                )
                await asyncio.sleep(delay)

        # Should never reach here
        raise ExternalServiceError(
            f"LLM call failed for {context}",
            error_code=ErrorCode.EXTERNAL_LLM_ERROR,
            original_error=last_exc,
        )


# ---------------------------------------------------------------------------
# Module-level helpers
# ---------------------------------------------------------------------------

_STOP_WORDS = frozenset(
    {
        # English
        "a",
        "an",
        "the",
        "and",
        "or",
        "but",
        "in",
        "on",
        "at",
        "to",
        "for",
        "of",
        "with",
        "by",
        "from",
        "is",
        "are",
        "was",
        "were",
        "be",
        "been",
        "being",
        "have",
        "has",
        "had",
        "do",
        "does",
        "did",
        "will",
        "would",
        "could",
        "should",
        "may",
        "might",
        "can",
        "this",
        "that",
        "these",
        "those",
        "i",
        "you",
        "he",
        "she",
        "it",
        "we",
        "they",
        "what",
        "how",
        "when",
        "where",
        "why",
        "which",
        "who",
        "not",
        "no",
        "so",
        "if",
        # Chinese particles / common words (simplified + traditional)
        "的",
        "了",
        "是",
        "在",
        "我",
        "你",
        "他",
        "她",
        "它",
        "我們",
        "你們",
        "他們",
        "這",
        "那",
        "有",
        "和",
        "與",
        "或",
        "但",
        "也",
        "都",
        "就",
        "不",
        "沒",
        "嗎",
        "呢",
        "吧",
        "啊",
        "哦",
        "嗯",
    }
)


def _extract_keywords(text: str, *, top_n: int = 20) -> set[str]:
    """Extract meaningful keywords from a text string.

    Splits on whitespace and common punctuation, lowercases tokens, removes
    stop words, and returns the ``top_n`` most frequent tokens as a set.

    Args:
        text: Input text.
        top_n: Maximum number of keywords to return.

    Returns:
        Set of keyword strings.
    """
    import re

    tokens = re.split(r"[\s\u3000\uff0c\u3001\u3002\uff01\uff1f,.\-_/|:;!?\"'()\[\]{}]+", text)
    counter: Counter[str] = Counter()
    for token in tokens:
        token = token.lower().strip()
        if len(token) >= 2 and token not in _STOP_WORDS:
            counter[token] += 1

    return {word for word, _ in counter.most_common(top_n)}


def _build_transcript(messages: list[Any], *, max_chars: int = 2000) -> str:
    """Build a compact conversation transcript string for LLM prompts.

    Args:
        messages: List of :class:`~app.core.database.ConversationMessage`
            objects.
        max_chars: Soft character limit.  The transcript is truncated at the
            last complete message that fits within this limit.

    Returns:
        Multi-line string with ``[role]: content`` lines.
    """
    lines: list[str] = []
    total = 0
    for msg in messages:
        role_label = "User" if msg.role == "user" else "Assistant"
        # Truncate very long individual messages
        content = msg.content[:500] + "…" if len(msg.content) > 500 else msg.content
        line = f"[{role_label}]: {content}"
        if total + len(line) > max_chars:
            break
        lines.append(line)
        total += len(line) + 1  # +1 for newline

    return "\n".join(lines)


def _build_recommendation_reason(shared_tags: list[str], keyword_overlap: int) -> str:
    """Build a short human-readable reason for a recommendation.

    Args:
        shared_tags: Tags shared between the two conversations.
        keyword_overlap: Number of overlapping keywords in titles.

    Returns:
        A short reason string.
    """
    parts: list[str] = []
    if shared_tags:
        tag_str = ", ".join(f"#{t}" for t in shared_tags[:3])
        parts.append(f"Shares tags: {tag_str}")
    if keyword_overlap > 0:
        parts.append(f"{keyword_overlap} overlapping topic keyword(s)")
    return "; ".join(parts) if parts else "Similar topic area"


def _safe_parse_json(text: str) -> dict[str, Any]:
    """Attempt to parse a JSON string, stripping markdown fences if present.

    Args:
        text: Raw LLM output that should contain JSON.

    Returns:
        Parsed dictionary, or an empty dict on failure.
    """
    cleaned = text.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    try:
        result = json.loads(cleaned)
        return result if isinstance(result, dict) else {}
    except (json.JSONDecodeError, ValueError):
        logger.warning("Failed to parse LLM JSON response", raw=text[:200])
        return {}
