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

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from openai import AsyncOpenAI

from app.core.config import settings
from app.core.errors import DatabaseError
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


from app.services._sc_analyse_mixin import AnalyseMixin
from app.services._sc_llm_mixin import LlmMixin


class SmartConversationService(AnalyseMixin, LlmMixin):
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
