"""
Unit tests for LLMService
Covers: evaluate_article, evaluate_batch (semaphore fix), generate_weekly_newsletter
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

from app.schemas.article import ArticleSchema, AIAnalysis
from app.services.llm_service import LLMService
from app.core.exceptions import LLMServiceError


def make_article(title="Test Article", url="https://example.com/article", tinkering_index=3):
    return ArticleSchema(
        title=title,
        url=url,
        content_preview="Some technical content preview",
        source_category="AI",
        source_name="TestSource",
    )


def make_hardcore_article(title="Hardcore Article", tinkering_index=4):
    article = make_article(title=title)
    article.ai_analysis = AIAnalysis(
        is_hardcore=True,
        reason="Has code and architecture discussion",
        actionable_takeaway="Deploy with Docker",
        tinkering_index=tinkering_index,
    )
    return article


# ---------------------------------------------------------------------------
# evaluate_article
# ---------------------------------------------------------------------------

class TestEvaluateArticle:
    @pytest.mark.asyncio
    async def test_returns_ai_analysis_on_success(self):
        """evaluate_article returns a valid AIAnalysis when LLM responds correctly."""
        service = LLMService.__new__(LLMService)
        mock_response = MagicMock()
        mock_response.choices[0].message.content = (
            '{"is_hardcore": true, "reason": "Has code", '
            '"actionable_takeaway": "Use it", "tinkering_index": 3}'
        )
        mock_client = MagicMock()
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
        service.client = mock_client

        result = await service.evaluate_article(make_article())

        assert isinstance(result, AIAnalysis)
        assert result.is_hardcore is True
        assert result.tinkering_index == 3

    @pytest.mark.asyncio
    async def test_returns_fallback_on_empty_response(self):
        """evaluate_article returns a safe fallback when LLM returns empty content."""
        service = LLMService.__new__(LLMService)
        mock_response = MagicMock()
        mock_response.choices[0].message.content = None
        mock_client = MagicMock()
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
        service.client = mock_client

        result = await service.evaluate_article(make_article())

        assert result.is_hardcore is False
        assert result.tinkering_index == 0

    @pytest.mark.asyncio
    async def test_returns_fallback_on_exception(self):
        """evaluate_article returns a safe fallback when LLM call raises."""
        service = LLMService.__new__(LLMService)
        mock_client = MagicMock()
        mock_client.chat.completions.create = AsyncMock(side_effect=Exception("timeout"))
        service.client = mock_client

        result = await service.evaluate_article(make_article())

        assert result.is_hardcore is False

    @pytest.mark.asyncio
    async def test_strips_markdown_code_block_from_response(self):
        """evaluate_article handles LLM responses wrapped in ```json blocks."""
        service = LLMService.__new__(LLMService)
        mock_response = MagicMock()
        mock_response.choices[0].message.content = (
            '```json\n{"is_hardcore": false, "reason": "Marketing", '
            '"actionable_takeaway": "", "tinkering_index": 0}\n```'
        )
        mock_client = MagicMock()
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
        service.client = mock_client

        result = await service.evaluate_article(make_article())

        assert result.is_hardcore is False


# ---------------------------------------------------------------------------
# evaluate_batch — semaphore fix verification
# ---------------------------------------------------------------------------

class TestEvaluateBatch:
    @pytest.mark.asyncio
    async def test_filters_non_hardcore_articles(self):
        """evaluate_batch returns only articles where is_hardcore is True."""
        service = LLMService.__new__(LLMService)

        call_count = 0

        async def fake_evaluate(article):
            nonlocal call_count
            call_count += 1
            # Only the first article is hardcore
            return AIAnalysis(
                is_hardcore=(call_count == 1),
                reason="reason",
                actionable_takeaway="",
                tinkering_index=1,
            )

        service.evaluate_article = fake_evaluate

        articles = [make_article(title=f"Article {i}") for i in range(3)]
        result = await service.evaluate_batch(articles)

        assert len(result) == 1
        assert result[0].ai_analysis.is_hardcore is True

    @pytest.mark.asyncio
    async def test_semaphore_limits_concurrency(self):
        """evaluate_batch never exceeds 5 concurrent evaluate_article calls."""
        service = LLMService.__new__(LLMService)

        active = 0
        max_active = 0

        async def fake_evaluate(article):
            nonlocal active, max_active
            active += 1
            max_active = max(max_active, active)
            await asyncio.sleep(0)  # yield to event loop
            active -= 1
            return AIAnalysis(is_hardcore=True, reason="r", actionable_takeaway="", tinkering_index=1)

        service.evaluate_article = fake_evaluate

        articles = [make_article(title=f"Article {i}") for i in range(10)]
        await service.evaluate_batch(articles)

        assert max_active <= 5, f"Concurrency exceeded semaphore limit: {max_active} > 5"

    @pytest.mark.asyncio
    async def test_returns_empty_list_when_no_articles(self):
        """evaluate_batch returns [] for empty input."""
        service = LLMService.__new__(LLMService)
        service.evaluate_article = AsyncMock()

        result = await service.evaluate_batch([])

        assert result == []
        service.evaluate_article.assert_not_called()

    @pytest.mark.asyncio
    async def test_all_articles_evaluated(self):
        """evaluate_batch calls evaluate_article for every article in the input."""
        service = LLMService.__new__(LLMService)
        evaluated_titles = []

        async def fake_evaluate(article):
            evaluated_titles.append(article.title)
            return AIAnalysis(is_hardcore=True, reason="r", actionable_takeaway="", tinkering_index=1)

        service.evaluate_article = fake_evaluate
        articles = [make_article(title=f"Article {i}") for i in range(5)]
        await service.evaluate_batch(articles)

        assert sorted(evaluated_titles) == sorted(a.title for a in articles)


# ---------------------------------------------------------------------------
# generate_weekly_newsletter
# ---------------------------------------------------------------------------

class TestGenerateWeeklyNewsletter:
    @pytest.mark.asyncio
    async def test_returns_placeholder_when_no_articles(self):
        """generate_weekly_newsletter returns a non-empty placeholder string for empty input."""
        service = LLMService.__new__(LLMService)
        service.client = MagicMock()

        result = await service.generate_weekly_newsletter([])

        assert isinstance(result, str)
        assert len(result) > 0

    @pytest.mark.asyncio
    async def test_returns_newsletter_on_success(self):
        """generate_weekly_newsletter returns LLM output when call succeeds."""
        service = LLMService.__new__(LLMService)
        mock_response = MagicMock()
        mock_response.choices[0].message.content = "# Weekly Newsletter\nSome content"
        mock_client = MagicMock()
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
        service.client = mock_client

        articles = [make_hardcore_article(title=f"Article {i}") for i in range(3)]
        result = await service.generate_weekly_newsletter(articles)

        assert "Weekly Newsletter" in result

    @pytest.mark.asyncio
    async def test_raises_llm_service_error_on_failure(self):
        """generate_weekly_newsletter raises LLMServiceError when LLM call fails."""
        service = LLMService.__new__(LLMService)
        mock_client = MagicMock()
        mock_client.chat.completions.create = AsyncMock(side_effect=Exception("API error"))
        service.client = mock_client

        articles = [make_hardcore_article()]
        with pytest.raises(LLMServiceError):
            await service.generate_weekly_newsletter(articles)

    @pytest.mark.asyncio
    async def test_sorts_by_tinkering_index_descending(self):
        """generate_weekly_newsletter sorts articles by tinkering_index descending before slicing top 7."""
        service = LLMService.__new__(LLMService)

        captured_draft = {}

        async def fake_create(**kwargs):
            captured_draft["user_content"] = kwargs["messages"][1]["content"]
            mock_response = MagicMock()
            mock_response.choices[0].message.content = "newsletter"
            return mock_response

        mock_client = MagicMock()
        mock_client.chat.completions.create = fake_create
        service.client = mock_client

        articles = [make_hardcore_article(title=f"Article {i}", tinkering_index=i) for i in range(1, 6)]
        await service.generate_weekly_newsletter(articles)

        # The first article mentioned in the draft should be the one with highest tinkering_index
        content = captured_draft["user_content"]
        idx_5 = content.find("Article 5")
        idx_1 = content.find("Article 1")
        assert idx_5 < idx_1, "Articles not sorted by tinkering_index descending"
