"""
Property-based tests for weekly_news_job.
Tests article page creation properties.
"""
import pytest
from hypothesis import given, settings as h_settings
from hypothesis import strategies as st
from unittest.mock import AsyncMock, MagicMock, patch

from app.schemas.article import ArticleSchema, AIAnalysis, ArticlePageResult
from app.core.exceptions import NotionServiceError


# ---------------------------------------------------------------------------
# Hypothesis strategies
# ---------------------------------------------------------------------------

def article_strategy():
    """Strategy for generating ArticleSchema with ai_analysis."""
    return st.builds(
        ArticleSchema,
        title=st.text(min_size=1, max_size=200),
        url=st.from_regex(r"https://[a-z]{3,10}\.[a-z]{2,4}/[a-z]{0,20}", fullmatch=True),
        content_preview=st.text(min_size=0, max_size=800),
        source_category=st.sampled_from(["AI", "DevOps", "Security", "Web", "Cloud"]),
        source_name=st.text(min_size=1, max_size=50),
        ai_analysis=st.builds(
            AIAnalysis,
            is_hardcore=st.just(True),
            reason=st.text(min_size=1, max_size=200),
            actionable_takeaway=st.text(min_size=0, max_size=200),
            tinkering_index=st.integers(min_value=1, max_value=5),
        ),
    )


# ---------------------------------------------------------------------------
# Property 12: Number of successfully created Pages = number of successful articles
# ---------------------------------------------------------------------------

# Feature: notion-article-pages-refactor, Property 12: Number of successfully created Pages = number of successful articles
@given(
    hardcore_articles=st.lists(article_strategy(), min_size=0, max_size=30),
    # Randomly decide which articles will fail (by index)
    failing_indices=st.sets(st.integers(min_value=0, max_value=29), max_size=10),
)
@h_settings(max_examples=100, deadline=None)
@pytest.mark.asyncio
async def test_page_count_matches_successful_articles(hardcore_articles, failing_indices):
    """**Validates: Requirements 2.1, 2.4**

    For any list of hardcore articles, the number of successfully created Notion Pages
    equals the number of articles that didn't fail during creation.
    
    Single article failures should not affect other articles.
    """
    from app.tasks.scheduler import weekly_news_job
    
    # Filter failing_indices to only valid indices for this list
    valid_failing_indices = {i for i in failing_indices if i < len(hardcore_articles)}
    expected_success_count = len(hardcore_articles) - len(valid_failing_indices)
    
    # Mock services
    mock_notion = MagicMock()
    mock_notion.get_active_feeds = AsyncMock(return_value=[MagicMock()])
    
    # Mock create_article_page to fail for specific indices
    call_count = [0]  # Use list to allow mutation in nested function
    
    async def mock_create_article_page(article, published_week):
        idx = call_count[0]
        call_count[0] += 1
        
        if idx in valid_failing_indices:
            raise NotionServiceError(f"Failed to create page for article {idx}")
        
        return (f"page-id-{idx}", f"https://notion.so/page-{idx}")
    
    mock_notion.create_article_page = mock_create_article_page
    mock_notion.build_article_list_notification = MagicMock(return_value="test notification")
    
    mock_rss = MagicMock()
    mock_rss.fetch_all_feeds = AsyncMock(return_value=[MagicMock()])
    
    mock_llm = MagicMock()
    mock_llm.evaluate_batch = AsyncMock(return_value=hardcore_articles)
    
    mock_channel = AsyncMock()
    mock_channel.send = AsyncMock()
    
    mock_bot = MagicMock()
    mock_bot.get_channel = MagicMock(return_value=mock_channel)
    
    mock_view = MagicMock()
    
    with patch("app.tasks.scheduler.NotionService", return_value=mock_notion), \
         patch("app.tasks.scheduler.RSSService", return_value=mock_rss), \
         patch("app.tasks.scheduler.LLMService", return_value=mock_llm), \
         patch("app.tasks.scheduler.bot", mock_bot), \
         patch("app.tasks.scheduler.MarkReadView", return_value=mock_view), \
         patch("app.tasks.scheduler.settings") as mock_settings:
        mock_settings.discord_channel_id = 123456789
        mock_settings.timezone = "Asia/Taipei"
        mock_settings.notion_weekly_digests_db_id = "some-db-id"
        
        await weekly_news_job()
    
    # Verify build_article_list_notification was called with correct number of successful pages
    if expected_success_count > 0 or len(hardcore_articles) == 0:
        mock_notion.build_article_list_notification.assert_called_once()
        call_args = mock_notion.build_article_list_notification.call_args
        article_pages_arg = call_args[0][0] if call_args[0] else call_args.kwargs.get("article_pages", [])
        
        assert len(article_pages_arg) == expected_success_count, (
            f"Expected {expected_success_count} successful pages, "
            f"but got {len(article_pages_arg)}. "
            f"Total articles: {len(hardcore_articles)}, "
            f"Failing indices: {valid_failing_indices}"
        )
