"""
Unit tests for RSS content extraction (content_preview field).
Validates that rss_service correctly extracts and strips HTML from
entry.content, entry.summary, and entry.description.
"""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest

from app.schemas.article import ArticleSchema, RSSSource
from app.services.rss_service import RSSService, _strip_html

# ---------------------------------------------------------------------------
# _strip_html helper
# ---------------------------------------------------------------------------


def test_strip_html_removes_tags():
    result = _strip_html("<p>Hello <b>world</b></p>")
    assert "Hello" in result and "world" in result and "<" not in result


def test_strip_html_plain_text_unchanged():
    text = "No HTML here"
    assert _strip_html(text) == text


def test_strip_html_empty_string():
    assert _strip_html("") == ""


# ---------------------------------------------------------------------------
# content_preview field on ArticleSchema
# ---------------------------------------------------------------------------


def test_article_schema_content_preview_default_none():
    article = ArticleSchema(
        title="T",
        url="https://example.com",
        feed_id=uuid4(),
        feed_name="F",
        category="C",
    )
    assert article.content_preview is None


def test_article_schema_content_preview_stored():
    article = ArticleSchema(
        title="T",
        url="https://example.com",
        feed_id=uuid4(),
        feed_name="F",
        category="C",
        content_preview="Some content here",
    )
    assert article.content_preview == "Some content here"


# ---------------------------------------------------------------------------
# _process_single_feed — content extraction
# ---------------------------------------------------------------------------

RECENT_DATE = datetime.now(UTC).strftime("%a, %d %b %Y %H:%M:%S GMT")


def _make_feed_xml(description: str = "", content: str = "") -> str:
    desc_tag = f"<description>{description}</description>" if description else ""
    content_tag = f"<content:encoded><![CDATA[{content}]]></content:encoded>" if content else ""
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:content="http://purl.org/rss/1.0/modules/content/">
  <channel>
    <title>Test</title>
    <item>
      <title>Article Title</title>
      <link>https://example.com/article</link>
      <pubDate>{RECENT_DATE}</pubDate>
      {desc_tag}
      {content_tag}
    </item>
  </channel>
</rss>"""


async def _parse_feed(xml: str) -> list[ArticleSchema]:
    service = RSSService(days_to_fetch=7)
    source = RSSSource(name="F", url="https://example.com/rss", category="C")
    feed_id = uuid4()

    mock_client = AsyncMock()
    mock_response = Mock()
    mock_response.text = xml
    mock_client.get = AsyncMock(return_value=mock_response)

    articles, _ = await service._process_single_feed(
        source, mock_client, {str(source.url): feed_id}
    )
    return articles


@pytest.mark.asyncio
async def test_content_preview_from_description():
    xml = _make_feed_xml(description="Plain text description")
    articles = await _parse_feed(xml)
    assert len(articles) == 1
    assert articles[0].content_preview == "Plain text description"


@pytest.mark.asyncio
async def test_content_preview_strips_html_from_description():
    xml = _make_feed_xml(description="<p>Hello <b>world</b></p>")
    articles = await _parse_feed(xml)
    assert len(articles) == 1
    assert "<" not in (articles[0].content_preview or "")
    assert "Hello" in (articles[0].content_preview or "")


@pytest.mark.asyncio
async def test_content_preview_none_when_no_description():
    xml = _make_feed_xml()  # no description, no content
    articles = await _parse_feed(xml)
    assert len(articles) == 1
    assert articles[0].content_preview is None


@pytest.mark.asyncio
async def test_content_preview_truncated_to_3000_chars():
    long_text = "x" * 5000
    xml = _make_feed_xml(description=long_text)
    articles = await _parse_feed(xml)
    assert len(articles) == 1
    assert len(articles[0].content_preview) == 3000
