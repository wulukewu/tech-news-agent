"""
Web scraper for extracting full article content when RSS description is insufficient.
Used as a fallback when content_preview < 200 chars.
"""

import logging
from html.parser import HTMLParser

import httpx

logger = logging.getLogger(__name__)

_SKIP_TAGS = {
    "script",
    "style",
    "nav",
    "header",
    "footer",
    "aside",
    "form",
    "button",
    "noscript",
    "iframe",
}

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
}


class _ArticleExtractor(HTMLParser):
    """Extracts readable text, skipping nav/script/style noise."""

    def __init__(self):
        super().__init__()
        self._skip_depth = 0
        self._parts: list[str] = []

    def handle_starttag(self, tag: str, attrs) -> None:
        if tag in _SKIP_TAGS:
            self._skip_depth += 1

    def handle_endtag(self, tag: str) -> None:
        if tag in _SKIP_TAGS and self._skip_depth > 0:
            self._skip_depth -= 1

    def handle_data(self, data: str) -> None:
        if self._skip_depth == 0:
            text = data.strip()
            if len(text) > 20:
                self._parts.append(text)

    def get_text(self) -> str:
        return " ".join(self._parts)


async def scrape_article(url: str, timeout: float = 10.0) -> str | None:
    """
    Fetch a URL and extract readable text (up to 3000 chars).
    Returns None if scraping fails or content is too short.
    """
    try:
        async with httpx.AsyncClient(follow_redirects=True) as client:
            response = await client.get(url, headers=HEADERS, timeout=timeout)
            response.raise_for_status()

            if "html" not in response.headers.get("content-type", ""):
                return None

            extractor = _ArticleExtractor()
            extractor.feed(response.text)
            text = extractor.get_text().strip()

            if len(text) < 100:
                return None

            return text[:3000]

    except Exception as e:
        logger.debug(f"Failed to scrape {url}: {e}")
        return None
