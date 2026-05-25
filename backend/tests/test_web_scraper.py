"""Unit tests for web_scraper.py"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.web_scraper import scrape_article


@pytest.mark.asyncio
async def test_scrape_article_strips_script_and_nav_content():
    # Long enough text to pass the 100 character minimum filter
    html = (
        "<html><body>"
        "<script>var x = 1;</script>"
        "<nav>Home About Contact Careers</nav>"
        "<p>" + "This is actual body content. " * 10 + "</p>"
        "</body></html>"
    )
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
    assert "var x" not in result
    assert "Home About" not in result
    assert "This is actual body content." in result


@pytest.mark.asyncio
async def test_scrape_article_ignores_short_content():
    # Content less than 100 characters should return None
    html = "<html><body><p>Too short</p></body></html>"
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

    assert result is None


@pytest.mark.asyncio
async def test_scrape_article_follows_meta_refresh_redirect():
    # first call returns redirect
    html1 = '<html><head><meta http-equiv="Refresh" content="0; url=\'https://example.com/redirected\'"/></head></html>'
    # second call returns actual content
    html2 = "<html><body><p>" + "This is redirected article content. " * 10 + "</p></body></html>"

    mock_response1 = MagicMock()
    mock_response1.text = html1
    mock_response1.headers = {"content-type": "text/html"}
    mock_response1.raise_for_status = MagicMock()

    mock_response2 = MagicMock()
    mock_response2.text = html2
    mock_response2.headers = {"content-type": "text/html"}
    mock_response2.raise_for_status = MagicMock()

    def get_side_effect(url, headers=None):
        if "redirected" in str(url):
            return mock_response2
        return mock_response1

    with patch("httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(side_effect=get_side_effect)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client_cls.return_value = mock_client

        result = await scrape_article("https://example.com/initial")

    assert result is not None
    assert "This is redirected article content." in result


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
