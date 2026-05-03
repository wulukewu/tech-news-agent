"""
Regression tests for three key bug fixes:

1. get_user_articles must NOT filter out articles with null tinkering_index
   (fix: notifications were empty when Groq TPD was exhausted)

2. weekly-insights API must only return status=completed records
   (fix: pending/failed records were shown in UI)

3. InsightReportGenerator must write pending→completed status
   (fix: interrupted jobs left stale pending records)
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

# ── 1. get_user_articles includes null tinkering_index ────────────────────────


def _make_supabase_mock(articles: list[dict], subscriptions: list[dict]) -> MagicMock:
    """Build a minimal Supabase client mock."""
    client = MagicMock()

    def table(name: str):
        tbl = MagicMock()
        tbl.select.return_value = tbl
        tbl.eq.return_value = tbl
        tbl.not_ = tbl
        tbl.in_.return_value = tbl
        tbl.gte.return_value = tbl
        tbl.order.return_value = tbl
        tbl.limit.return_value = tbl

        if name == "user_subscriptions":
            tbl.execute.return_value = MagicMock(data=subscriptions)
        elif name == "dm_sent_articles":
            tbl.execute.return_value = MagicMock(data=[])
        elif name == "articles":
            tbl.execute.return_value = MagicMock(data=articles)
        else:
            tbl.execute.return_value = MagicMock(data=[])
        return tbl

    client.table.side_effect = table
    return client


@pytest.mark.asyncio
async def test_get_user_articles_includes_null_tinkering_index():
    """
    Regression: articles with tinkering_index=None must NOT be filtered out.
    Previously .not_.is_("tinkering_index", "null") excluded them, causing
    empty notifications when Groq TPD was exhausted.
    """
    feed_id = str(uuid4())
    article_id = str(uuid4())

    articles = [
        {
            "id": article_id,
            "title": "Test Article",
            "url": "https://example.com",
            "published_at": "2026-05-04T00:00:00+00:00",
            "tinkering_index": None,  # ← the key case
            "ai_summary": None,
            "feed_id": feed_id,
            "feeds": {"category": "Tech"},
        }
    ]
    subscriptions = [{"feed_id": feed_id}]

    from app.services._mixins.article_mixin import ArticleMixin

    mixin = ArticleMixin.__new__(ArticleMixin)
    mixin.client = _make_supabase_mock(articles, subscriptions)
    mixin.logger = MagicMock()
    mixin.get_or_create_user = AsyncMock(return_value=uuid4())

    result = await mixin.get_user_articles(discord_id="123456789", frequency="daily")

    assert len(result) == 1, "Article with null tinkering_index must be included"
    assert result[0].title == "Test Article"


# ── 2. weekly-insights API filters out non-completed records ──────────────────


def test_weekly_insights_latest_query_filters_completed():
    """
    Regression: /weekly-insights/latest must only return status=completed rows.
    Previously it returned pending/failed records, showing 0-article reports in UI.
    """
    import inspect

    import app.api.weekly_insights as module

    source = inspect.getsource(module.get_latest_insights)
    assert (
        '.eq("status", "completed")' in source
    ), "get_latest_insights must filter by status=completed"


def test_weekly_insights_history_query_filters_completed():
    """
    Regression: /weekly-insights/history must only return status=completed rows.
    """
    import inspect

    import app.api.weekly_insights as module

    source = inspect.getsource(module.get_insights_history)
    assert (
        '.eq("status", "completed")' in source
    ), "get_insights_history must filter by status=completed"


# ── 3. InsightReportGenerator writes pending→completed status ─────────────────


@pytest.mark.asyncio
async def test_report_generator_inserts_pending_then_completes():
    """
    Regression: generate() must insert a pending record before running the
    pipeline, then update it to completed on success.
    """
    from app.qa_agent.weekly_insights.report_generator import InsightReportGenerator

    generator = InsightReportGenerator.__new__(InsightReportGenerator)
    generator.collector = MagicMock()
    generator.analyzer = MagicMock()
    generator.clusterer = MagicMock()
    generator.trend_detector = MagicMock()
    generator.personalization = MagicMock()

    pending_id = str(uuid4())
    inserted_statuses: list[str] = []

    async def fake_insert_pending(*_a, **_kw):
        inserted_statuses.append("pending")
        return pending_id

    async def fake_run_pipeline(*_a, **_kw):
        return {
            "period_start": "2026-04-27T00:00:00+00:00",
            "period_end": "2026-05-04T00:00:00+00:00",
            "article_count": 5,
            "executive_summary": "Test",
            "clusters": [],
            "trends": [],
            "missed_articles": [],
            "trend_data": [],
            "created_at": "2026-05-04T00:00:00+00:00",
        }

    async def fake_save_report(_report, pid):
        inserted_statuses.append("completed")
        return pid

    generator._insert_pending = fake_insert_pending
    generator._run_pipeline = fake_run_pipeline
    generator._save_report = fake_save_report

    result = await generator.generate()

    assert "pending" in inserted_statuses, "_insert_pending must be called"
    assert "completed" in inserted_statuses, "_save_report must be called"
    assert inserted_statuses.index("pending") < inserted_statuses.index(
        "completed"
    ), "pending must come before completed"
    assert result["id"] == pending_id
