"""Mixin extracted from smart_conversation.py."""
from __future__ import annotations

import asyncio
import json
from collections import Counter
from typing import Any, Optional

from app.core.errors import ErrorCode, ExternalServiceError
from app.core.logger import get_logger

logger = get_logger(__name__)


class LlmMixin:
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
