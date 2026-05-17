"""Unit tests for web_scraper.py"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.web_scraper import _ArticleExtractor, scrape_article


def test_extractor_strips_script_content():
    e = _ArticleExtractor()
    e.feed("<script>var x = 1;</script><p>Real content here that is long enough</p>")
    assert "var x" not in e.get_text()
    assert "Real content" in e.get_text()


def test_extractor_skips_nav():
    e = _ArticleExtractor()
    e.feed("<nav>Home About Contact</nav><p>Article body text that is long enough to pass</p>")
    text = e.get_text()
    assert "Article body text" in text


def test_extractor_ignores_short_noise():
    e = _ArticleExtractor()
    e.feed("<p>Hi</p><p>This is a longer paragraph that should be included in output</p>")
    text = e.get_text()
    # "Hi" is < 20 chars, should be ignored
    assert "Hi" not in text
    assert "longer paragraph" in text


@pytest.mark.asyncio
async def test_scrape_article_returns_text_on_success():
    html = "<html><body><p>" + "This is article content. " * 20 + "</p></body></html>"
    mock_response = MagicMock()
    mock_response.text = html
    mock_response.headers = {"content-type": "text/html"}
    mock_response.raise_for_status = MagicMock()

    with patch("httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client_cls.return_value = mock_client

        result = await scrape_article("https://example.com/article")

    assert result is not None
    assert "article content" in result


@pytest.mark.asyncio
async def test_scrape_article_returns_none_on_http_error():
    with patch("httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(side_effect=Exception("Connection refused"))
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client_cls.return_value = mock_client

        result = await scrape_article("https://example.com/article")

    assert result is None


@pytest.mark.asyncio
async def test_scrape_article_truncates_to_3000():
    long_text = "word " * 2000  # ~10000 chars
    html = f"<html><body><p>{long_text}</p></body></html>"
    mock_response = MagicMock()
    mock_response.text = html
    mock_response.headers = {"content-type": "text/html"}
    mock_response.raise_for_status = MagicMock()

    with patch("httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client_cls.return_value = mock_client

        result = await scrape_article("https://example.com/article")

    assert result is not None
    assert len(result) <= 3000


@pytest.mark.asyncio
async def test_scrape_article_returns_none_for_non_html():
    mock_response = MagicMock()
    mock_response.text = '{"key": "value"}'
    mock_response.headers = {"content-type": "application/json"}
    mock_response.raise_for_status = MagicMock()

    with patch("httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client_cls.return_value = mock_client

        result = await scrape_article("https://example.com/api")

    assert result is None
