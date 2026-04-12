"""
Property-based tests and unit tests for build_article_list_notification.
Tests Discord message length and content requirements.
"""

from hypothesis import given
from hypothesis import settings as h_settings
from hypothesis import strategies as st

from app.schemas.article import ArticlePageResult
from app.services.notion_service import NotionService

# ---------------------------------------------------------------------------
# Hypothesis strategies
# ---------------------------------------------------------------------------

article_page_result_strategy = st.builds(
    ArticlePageResult,
    page_id=st.text(min_size=1, max_size=50),
    page_url=st.text(min_size=10, max_size=500).map(lambda s: "https://notion.so/" + s[:100]),
    title=st.text(min_size=1, max_size=200),
    category=st.sampled_from(["AI", "DevOps", "Security", "Web", "Cloud", "Backend", "Frontend"]),
    tinkering_index=st.integers(min_value=0, max_value=5),
)

stats_strategy = st.fixed_dictionaries(
    {
        "total_fetched": st.integers(min_value=0, max_value=1000),
        "hardcore_count": st.integers(min_value=0, max_value=500),
    }
)


# ---------------------------------------------------------------------------
# Property 11: Discord 通知訊息長度不超過 2000 字元（任意文章數量）
# ---------------------------------------------------------------------------


# Feature: notion-article-pages-refactor, Property 11: Discord 通知訊息長度不超過 2000 字元（任意文章數量）
@given(
    article_pages=st.lists(article_page_result_strategy, min_size=0, max_size=100),
    stats=stats_strategy,
)
@h_settings(max_examples=5)
def test_article_list_notification_length(article_pages, stats):
    """Validates: Requirements 3.2

    For any list of ArticlePageResult (with any number of articles),
    build_article_list_notification output length ≤ 2000 characters.
    """
    message = NotionService.build_article_list_notification(article_pages, stats)
    assert len(message) <= 2000, (
        f"Discord notification length {len(message)} exceeds 2000 chars. "
        f"articles={len(article_pages)}"
    )


# ---------------------------------------------------------------------------
# Unit tests for build_article_list_notification
# ---------------------------------------------------------------------------


def test_build_article_list_notification_normal_mode():
    """Test normal mode with few articles (should not truncate)."""
    article_pages = [
        ArticlePageResult(
            page_id="page1",
            page_url="https://notion.so/article1",
            title="Building a RAG System with Rust",
            category="AI",
            tinkering_index=4,
        ),
        ArticlePageResult(
            page_id="page2",
            page_url="https://notion.so/article2",
            title="Kubernetes 1.30 新功能解析",
            category="DevOps",
            tinkering_index=3,
        ),
    ]
    stats = {
        "total_fetched": 42,
        "hardcore_count": 7,
    }

    message = NotionService.build_article_list_notification(article_pages, stats)

    # Check message structure
    assert "本週技術週報已發布" in message
    assert "本週統計：抓取 42 篇，精選 7 篇" in message
    assert "精選文章：" in message
    assert "1. [AI] Building a RAG System with Rust" in message
    assert "https://notion.so/article1" in message
    assert "2. [DevOps] Kubernetes 1.30 新功能解析" in message
    assert "https://notion.so/article2" in message

    # Should not be truncated
    assert "...（共" not in message

    # Check length
    assert len(message) <= 2000


def test_build_article_list_notification_truncation_mode():
    """Test truncation mode with many articles exceeding 2000 chars."""
    # Create many articles with long titles and URLs to exceed 2000 chars
    article_pages = []
    for i in range(50):
        article_pages.append(
            ArticlePageResult(
                page_id=f"page{i}",
                page_url=f"https://notion.so/very-long-article-url-{i}-with-extra-padding-to-make-it-longer",
                title=f"Very Long Article Title Number {i} With Extra Words To Make It Longer And Exceed Character Limits",
                category="AI",
                tinkering_index=3,
            )
        )

    stats = {
        "total_fetched": 100,
        "hardcore_count": 50,
    }

    message = NotionService.build_article_list_notification(article_pages, stats)

    # Check message structure
    assert "本週技術週報已發布" in message
    assert "本週統計：抓取 100 篇，精選 50 篇" in message
    assert "精選文章：" in message

    # Should be truncated
    assert "...（共 50 篇，查看 Notion 資料庫以瀏覽完整列表）" in message

    # Check length
    assert len(message) <= 2000


def test_build_article_list_notification_empty_list():
    """Test with empty article list."""
    article_pages = []
    stats = {
        "total_fetched": 42,
        "hardcore_count": 0,
    }

    message = NotionService.build_article_list_notification(article_pages, stats)

    # Check message structure
    assert "本週技術週報已發布" in message
    assert "本週統計：抓取 42 篇，精選 0 篇" in message
    assert "精選文章：" in message

    # Should not have any article entries
    assert "1. [" not in message

    # Check length
    assert len(message) <= 2000
