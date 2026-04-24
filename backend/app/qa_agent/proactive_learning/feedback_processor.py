"""
Feedback Processor

Parses user text responses to extract preference signals using LLM.
Requirements: 4.1, 4.2, 4.3, 4.4, 11.1, 11.2, 11.3, 11.4, 11.5
"""

import json
import logging
from typing import Any

from openai import AsyncOpenAI

from app.core.config import settings

logger = logging.getLogger(__name__)

PARSE_MODEL = "llama-3.1-8b-instant"

SYSTEM_PROMPT = """You are a preference signal extractor.
Given a user's response to a question about their reading preferences, extract signals.
Return ONLY valid JSON:
{
  "sentiment": "positive|negative|neutral|mixed",
  "interested_topics": ["topic1"],
  "disinterested_topics": ["topic2"],
  "weight_adjustments": {"topic": 0.2},
  "needs_clarification": false
}
weight_adjustments: positive float = increase interest, negative = decrease.
Range: -1.0 to 1.0"""


class FeedbackProcessor:
    """Extracts preference signals from user free-text responses."""

    def __init__(self):
        self.llm = AsyncOpenAI(
            base_url="https://api.groq.com/openai/v1",
            api_key=settings.groq_api_key,
            timeout=30,
        )

    async def process(
        self,
        question: str,
        response: str,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Parse user response and return structured preference signals.

        Returns:
            {sentiment, interested_topics, disinterested_topics,
             weight_adjustments, needs_clarification}
        """
        user_msg = f"Question: {question}\nUser response: {response}"
        if context:
            user_msg += f"\nContext: {json.dumps(context)}"

        try:
            resp = await self.llm.chat.completions.create(
                model=PARSE_MODEL,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_msg},
                ],
                max_tokens=200,
                temperature=0.1,
            )
            raw = resp.choices[0].message.content or "{}"
            raw = raw.strip()
            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]
            data = json.loads(raw)
        except Exception as exc:
            logger.warning("Feedback processing failed: %s", exc)
            data = {}

        return {
            "sentiment": data.get("sentiment", "neutral"),
            "interested_topics": data.get("interested_topics", []),
            "disinterested_topics": data.get("disinterested_topics", []),
            "weight_adjustments": data.get("weight_adjustments", {}),
            "needs_clarification": data.get("needs_clarification", False),
        }
