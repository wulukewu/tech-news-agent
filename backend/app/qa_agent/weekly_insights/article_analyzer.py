"""
Article Analyzer

Extracts themes, technologies, and topics from individual articles using LLM.
Requirements: 1.2, 1.3, 1.4, 10.1, 10.2
"""

import json
import logging
from typing import Any

from openai import AsyncOpenAI

from app.core.config import settings

logger = logging.getLogger(__name__)

ANALYZE_MODEL = "llama-3.1-8b-instant"

SYSTEM_PROMPT = """You are a technical article analyzer. Extract structured information from article titles and summaries.
Return ONLY valid JSON with this exact structure:
{
  "themes": ["theme1", "theme2"],
  "technologies": ["tech1", "tech2"],
  "domain": "frontend|backend|devops|ai_ml|security|mobile|database|cloud|other",
  "keywords": ["kw1", "kw2", "kw3"]
}
Normalize all output to English. Keep arrays concise (max 5 items each)."""


class ArticleAnalyzer:
    """Extracts themes and topics from articles using LLM."""

    def __init__(self):
        self.client = AsyncOpenAI(
            base_url="https://api.groq.com/openai/v1",
            api_key=settings.groq_api_key,
            timeout=30,
        )

    async def analyze_article(self, article: dict[str, Any]) -> dict[str, Any]:
        """
        Analyze a single article and extract themes/technologies.

        Returns the article dict enriched with 'themes', 'technologies',
        'domain', and 'keywords' fields.
        """
        title = article.get("title", "")
        summary = article.get("ai_summary", "")
        content = f"Title: {title}\nSummary: {summary}"

        try:
            response = await self.client.chat.completions.create(
                model=ANALYZE_MODEL,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": content},
                ],
                max_tokens=200,
                temperature=0.1,
            )
            raw = response.choices[0].message.content or "{}"
            # Strip markdown code fences if present
            raw = raw.strip()
            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]
            data = json.loads(raw)
        except Exception as exc:
            logger.warning("Failed to analyze article '%s': %s", title, exc)
            data = {}

        return {
            **article,
            "themes": data.get("themes", []),
            "technologies": data.get("technologies", []),
            "domain": data.get("domain", "other"),
            "keywords": data.get("keywords", []),
        }

    async def analyze_articles(
        self, articles: list[dict[str, Any]], batch_size: int = 5
    ) -> list[dict[str, Any]]:
        """Analyze a list of articles in small batches with delay to respect Groq TPM limits.
        Falls back to empty themes on rate limit so the keyword fallback in the generator kicks in.
        """
        import asyncio

        results: list[dict[str, Any]] = []
        rate_limited = False  # once we hit 429, skip remaining LLM calls

        for i in range(0, len(articles), batch_size):
            batch = articles[i : i + batch_size]

            if rate_limited:
                # Skip LLM entirely for remaining articles; generator will use keyword fallback
                for a in batch:
                    results.append(
                        {**a, "themes": [], "technologies": [], "domain": "other", "keywords": []}
                    )
                continue

            analyzed = await asyncio.gather(
                *[self.analyze_article(a) for a in batch],
                return_exceptions=True,
            )
            for original, result in zip(batch, analyzed):
                if isinstance(result, Exception):
                    logger.warning("Analysis failed for article: %s", result)
                    results.append(
                        {
                            **original,
                            "themes": [],
                            "technologies": [],
                            "domain": "other",
                            "keywords": [],
                        }
                    )
                else:
                    results.append(result)

            # Check if any article in this batch hit a rate limit
            if any(isinstance(r, Exception) and "rate_limit" in str(r).lower() for r in analyzed):
                rate_limited = True
                logger.info("Rate limit hit — switching to keyword fallback for remaining articles")
                continue

            if i + batch_size < len(articles):
                await asyncio.sleep(12)
        return results
