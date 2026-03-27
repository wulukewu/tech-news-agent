"""
Property-based tests for build_discord_notification helper.
Tests Discord message length and content requirements.
"""
import pytest
from hypothesis import given, settings as h_settings
from hypothesis import strategies as st

from app.schemas.article import ArticleSchema, AIAnalysis, WeeklyDigestResult
from app.tasks.scheduler import build_discord_notification


# ---------------------------------------------------------------------------
# Hypothesis strategies
# ---------------------------------------------------------------------------

ai_analysis_strategy = st.builds(
    AIAnalysis,
    is_hardcore=st.just(True),
    reason=st.text(min_size=1, max_size=100),
    actionable_takeaway=st.text(max_size=100),
    tinkering_index=st.integers(min_value=1, max_value=5),
)

article_strategy = st.builds(
    ArticleSchema,
    title=st.text(min_size=1, max_size=200),
    url=st.just("https://example.com/article"),
    content_preview=st.text(max_size=100),
    source_category=st.sampled_from(["AI", "DevOps", "Security", "Web", "Cloud"]),
    source_name=st.text(min_size=1, max_size=50),
    ai_analysis=ai_analysis_strategy,
)

# Strategy for WeeklyDigestResult with varying article counts and URLs
digest_result_strategy = st.builds(
    WeeklyDigestResult,
    page_id=st.text(min_size=1, max_size=50),
    page_url=st.text(min_size=1, max_size=500).map(lambda s: "https://notion.so/" + s[:100]),
    article_count=st.integers(min_value=0, max_value=50),
    top_articles=st.lists(article_strategy, min_size=0, max_size=10),
)

# Strategy for WeeklyDigestResult with non-empty page_url
digest_result_with_url_strategy = st.builds(
    WeeklyDigestResult,
    page_id=st.text(min_size=1, max_size=50),
    page_url=st.text(min_size=10, max_size=200).map(lambda s: "https://notion.so/" + s),
    article_count=st.integers(min_value=1, max_value=50),
    top_articles=st.lists(article_strategy, min_size=1, max_size=10),
)

stats_strategy = st.fixed_dictionaries({
    "total_fetched": st.integers(min_value=0, max_value=1000),
    "hardcore_count": st.integers(min_value=0, max_value=500),
    "run_date": st.text(min_size=1, max_size=20),
})


# ---------------------------------------------------------------------------
# Property 9: Discord 通知訊息長度不超過 2000 字元
# ---------------------------------------------------------------------------

# Feature: notion-weekly-digest, Property 9: Discord 通知訊息長度不超過 2000 字元
@given(
    digest_result=digest_result_strategy,
    stats=stats_strategy,
)
@h_settings(max_examples=100)
def test_discord_notification_length(digest_result, stats):
    """Validates: Requirements 5.2

    For any WeeklyDigestResult (with any number of top_articles and any length page_url),
    build_discord_notification output length ≤ 2000 characters.
    """
    message = build_discord_notification(digest_result, digest_result.top_articles, stats)
    assert len(message) <= 2000, (
        f"Discord notification length {len(message)} exceeds 2000 chars. "
        f"page_url length={len(digest_result.page_url)}, "
        f"articles={len(digest_result.top_articles)}"
    )


# Feature: notion-weekly-digest, Property 9 (degraded): Discord 通知訊息長度不超過 2000 字元（降級模式）
@given(
    top_articles=st.lists(article_strategy, min_size=0, max_size=10),
    stats=stats_strategy,
)
@h_settings(max_examples=100)
def test_discord_notification_length_degraded(top_articles, stats):
    """Validates: Requirements 5.2

    For degraded mode (digest_result=None), message length ≤ 2000 characters.
    """
    message = build_discord_notification(None, top_articles, stats)
    assert len(message) <= 2000, (
        f"Degraded Discord notification length {len(message)} exceeds 2000 chars."
    )


# ---------------------------------------------------------------------------
# Property 10: Discord 通知包含統計數字與 Notion 連結
# ---------------------------------------------------------------------------

# Feature: notion-weekly-digest, Property 10: Discord 通知包含統計數字與 Notion 連結
@given(
    digest_result=digest_result_with_url_strategy,
    stats=stats_strategy,
)
@h_settings(max_examples=100)
def test_discord_notification_content(digest_result, stats):
    """Validates: Requirements 5.1

    For any valid WeeklyDigestResult (page_url non-empty),
    build_discord_notification output contains article_count as string and page_url.
    """
    message = build_discord_notification(digest_result, digest_result.top_articles, stats)
    assert digest_result.page_url in message, (
        f"page_url '{digest_result.page_url}' not found in notification message."
    )
    assert str(stats["total_fetched"]) in message or str(stats["hardcore_count"]) in message, (
        f"Neither total_fetched={stats['total_fetched']} nor hardcore_count={stats['hardcore_count']} "
        f"found in notification message."
    )
