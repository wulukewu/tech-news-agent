"""
Web scraper for extracting full article content when RSS description is insufficient.
Used as a fallback when content_preview < 200 chars.
"""

import logging
import re
from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

# Complete browser-like headers to bypass Cloudflare/WAF protections
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Connection": "keep-alive",
}

_NOISE_TAGS = [
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
    "svg",
]


async def scrape_article(url: str, timeout: float = 10.0, max_redirects: int = 3) -> str | None:
    """
    Fetch a URL and extract readable text using BeautifulSoup (up to 3000 chars).
    Supports recursive parsing of HTML meta-refresh redirects.
    Returns None if scraping fails or content is too short.
    """
    if max_redirects < 0:
        logger.warning(f"Max redirect limit reached for {url}")
        return None

    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=timeout) as client:
            response = await client.get(url, headers=HEADERS)
            response.raise_for_status()

            if "html" not in response.headers.get("content-type", "").lower():
                return None

            soup = BeautifulSoup(response.text, "html.parser")

            # Check for HTML meta-refresh redirects
            refresh_tag = soup.find(
                "meta", attrs={"http-equiv": lambda x: x and x.lower() == "refresh"}
            )
            if refresh_tag:
                content = refresh_tag.get("content", "")
                # Match e.g. "0; url='https://...'" or "0;url=..."
                match = re.search(r"url=['\"]?([^'\";]+)['\"]?", content, re.I)
                if match:
                    redirect_url = urljoin(url, match.group(1).strip())
                    logger.info(
                        f"Following HTML meta refresh redirect from {url} to {redirect_url}"
                    )
                    return await scrape_article(
                        redirect_url, timeout=timeout, max_redirects=max_redirects - 1
                    )

            # Decompose noise tags in-place
            for element in soup(_NOISE_TAGS):
                element.decompose()

            # Extract clean readable text
            text = " ".join(soup.get_text(separator=" ").split())

            if len(text) < 100:
                return None

            return text[:3000]

    except Exception as e:
        logger.debug(f"Failed to scrape {url}: {e}")
        return None
