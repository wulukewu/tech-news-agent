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
    from uuid import uuid4
    return ArticleSchema(
        title=title,
        url=url,
        feed_id=uuid4(),
        feed_name="TestSource",
        category="AI",
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
# generate_summary
# ---------------------------------------------------------------------------

class TestGenerateSummary:
    @pytest.mark.asyncio
    async def test_returns_string_on_success(self):
        """generate_summary returns a non-empty string when LLM responds."""
        service = LLMService.__new__(LLMService)
        mock_response = MagicMock()
        mock_response.choices[0].message.content = "這是一篇關於 AI 的技術摘要"
        mock_client = MagicMock()
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
        service.client = mock_client

        result = await service.generate_summary(make_article())

        assert isinstance(result, str)
        assert result == "這是一篇關於 AI 的技術摘要"

    @pytest.mark.asyncio
    async def test_returns_none_on_empty_response(self):
        """generate_summary returns None when LLM returns empty content."""
        service = LLMService.__new__(LLMService)
        mock_response = MagicMock()
        mock_response.choices[0].message.content = ""
        mock_client = MagicMock()
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
        service.client = mock_client

        result = await service.generate_summary(make_article())

        assert result is None

    @pytest.mark.asyncio
    async def test_returns_none_on_exception(self):
        """generate_summary returns None when LLM call raises."""
        service = LLMService.__new__(LLMService)
        mock_client = MagicMock()
        mock_client.chat.completions.create = AsyncMock(side_effect=Exception("API error"))
        service.client = mock_client

        result = await service.generate_summary(make_article())

        assert result is None

    @pytest.mark.asyncio
    async def test_uses_summarize_model(self):
        """generate_summary uses SUMMARIZE_MODEL (llama-3.3-70b-versatile)."""
        from app.services.llm_service import SUMMARIZE_MODEL

        service = LLMService.__new__(LLMService)
        captured = {}

        async def fake_create(**kwargs):
            captured["model"] = kwargs["model"]
            mock_response = MagicMock()
            mock_response.choices[0].message.content = "摘要"
            return mock_response

        mock_client = MagicMock()
        mock_client.chat.completions.create = fake_create
        service.client = mock_client

        await service.generate_summary(make_article())

        assert captured["model"] == SUMMARIZE_MODEL
        assert captured["model"] == "llama-3.3-70b-versatile"

    @pytest.mark.asyncio
    async def test_prompt_includes_title_and_category(self):
        """generate_summary includes title and category in user prompt."""
        service = LLMService.__new__(LLMService)
        captured = {}

        async def fake_create(**kwargs):
            captured["user"] = kwargs["messages"][1]["content"]
            mock_response = MagicMock()
            mock_response.choices[0].message.content = "摘要"
            return mock_response

        mock_client = MagicMock()
        mock_client.chat.completions.create = fake_create
        service.client = mock_client

        article = make_article(title="My Title")
        article.category = "DevOps"
        await service.generate_summary(article)

        assert "My Title" in captured["user"]
        assert "DevOps" in captured["user"]

    @pytest.mark.asyncio
    async def test_includes_ai_analysis_when_available(self):
        """generate_summary includes ai_analysis info in prompt when available."""
        service = LLMService.__new__(LLMService)
        captured = {}

        async def fake_create(**kwargs):
            captured["user"] = kwargs["messages"][1]["content"]
            mock_response = MagicMock()
            mock_response.choices[0].message.content = "摘要"
            return mock_response

        mock_client = MagicMock()
        mock_client.chat.completions.create = fake_create
        service.client = mock_client

        article = make_hardcore_article(title="Test Article", tinkering_index=4)
        await service.generate_summary(article)

        assert "AI 初步評估" in captured["user"]
        assert "折騰指數" in captured["user"]
        assert "4 / 5" in captured["user"]


# ---------------------------------------------------------------------------
# evaluate_batch — semaphore fix verification
# ---------------------------------------------------------------------------

class TestEvaluateBatch:
    @pytest.mark.asyncio
    async def test_returns_all_articles_including_non_hardcore(self):
        """evaluate_batch returns ALL articles (both hardcore and non-hardcore)."""
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
                tinkering_index=call_count,
            )

        async def fake_generate_summary(article):
            return f"Summary for {article.title}"

        service.evaluate_article = fake_evaluate
        service.generate_summary = fake_generate_summary

        articles = [make_article(title=f"Article {i}") for i in range(3)]
        result = await service.evaluate_batch(articles)

        # Should return all 3 articles, not just the hardcore one
        assert len(result) == 3
        assert result[0].ai_analysis.is_hardcore is True
        assert result[1].ai_analysis.is_hardcore is False
        assert result[2].ai_analysis.is_hardcore is False
        # All should have summaries
        assert all(a.ai_summary is not None for a in result)

    @pytest.mark.asyncio
    async def test_sets_null_on_api_failure(self):
        """evaluate_batch sets tinkering_index and ai_summary to NULL on API failure."""
        service = LLMService.__new__(LLMService)

        call_count = 0

        async def fake_evaluate(article):
            nonlocal call_count
            call_count += 1
            # First article succeeds, second fails
            if call_count == 2:
                raise Exception("API error")
            return AIAnalysis(
                is_hardcore=True,
                reason="reason",
                actionable_takeaway="",
                tinkering_index=3,
            )

        summary_call_count = 0

        async def fake_generate_summary(article):
            nonlocal summary_call_count
            summary_call_count += 1
            # Summary generation also fails for first article
            if summary_call_count == 1:
                raise Exception("Summary API error")
            return "Test summary"

        service.evaluate_article = fake_evaluate
        service.generate_summary = fake_generate_summary

        articles = [make_article(title=f"Article {i}") for i in range(2)]
        result = await service.evaluate_batch(articles)

        # Both articles should be returned
        assert len(result) == 2
        
        # First article should have analysis but no summary (summary failed)
        assert result[0].ai_analysis is not None
        assert result[0].tinkering_index == 3
        assert result[0].ai_summary is None
        
        # Second article should have NULL tinkering_index (evaluation failed) but has summary
        assert result[1].ai_analysis is None
        assert result[1].tinkering_index is None
        assert result[1].ai_summary == "Test summary"

    @pytest.mark.asyncio
    async def test_logs_warning_when_30_percent_fail(self, caplog):
        """evaluate_batch logs warning when more than 30% of articles fail."""
        import logging
        caplog.set_level(logging.WARNING)
        
        service = LLMService.__new__(LLMService)

        call_count = 0

        async def fake_evaluate(article):
            nonlocal call_count
            call_count += 1
            # Fail 4 out of 10 articles (40%)
            if call_count <= 4:
                raise Exception("API error")
            return AIAnalysis(
                is_hardcore=True,
                reason="reason",
                actionable_takeaway="",
                tinkering_index=3,
            )

        async def fake_generate_summary(article):
            return "Test summary"

        service.evaluate_article = fake_evaluate
        service.generate_summary = fake_generate_summary

        articles = [make_article(title=f"Article {i}") for i in range(10)]
        result = await service.evaluate_batch(articles)

        # All articles should be returned
        assert len(result) == 10
        
        # Check that warning was logged for tinkering_index failures
        assert any("High tinkering_index failure rate" in record.message for record in caplog.records)
        assert any("4/10" in record.message for record in caplog.records)

    @pytest.mark.asyncio
    async def test_logs_error_with_article_title_and_url_on_failure(self, caplog):
        """evaluate_batch logs error with article title and URL when API fails (Requirement 8.1)."""
        import logging
        caplog.set_level(logging.ERROR)
        
        service = LLMService.__new__(LLMService)

        async def fake_evaluate(article):
            raise Exception("API connection timeout")

        async def fake_generate_summary(article):
            return "Test summary"

        service.evaluate_article = fake_evaluate
        service.generate_summary = fake_generate_summary

        article = make_article(title="Test Article Title", url="https://example.com/test-article")
        result = await service.evaluate_batch([article])

        # Article should be returned with NULL tinkering_index
        assert len(result) == 1
        assert result[0].tinkering_index is None
        
        # Check that error was logged with article title and URL
        error_logs = [record for record in caplog.records if record.levelname == "ERROR"]
        assert len(error_logs) > 0
        
        # Verify the error log contains both title and URL
        error_message = error_logs[0].message
        assert "Test Article Title" in error_message
        assert "https://example.com/test-article" in error_message
        assert "Failed to evaluate tinkering_index" in error_message

    @pytest.mark.asyncio
    async def test_logs_success_and_failure_counts(self, caplog):
        """evaluate_batch logs counts of successful and failed articles (Requirements 3.8, 8.7)."""
        import logging
        caplog.set_level(logging.INFO)
        
        service = LLMService.__new__(LLMService)

        call_count = 0

        async def fake_evaluate(article):
            nonlocal call_count
            call_count += 1
            # Fail 2 out of 5 articles
            if call_count in [2, 4]:
                raise Exception("API error")
            return AIAnalysis(
                is_hardcore=True,
                reason="reason",
                actionable_takeaway="",
                tinkering_index=3,
            )

        summary_call_count = 0

        async def fake_generate_summary(article):
            nonlocal summary_call_count
            summary_call_count += 1
            # Fail 1 out of 5 summaries
            if summary_call_count == 3:
                raise Exception("Summary API error")
            return "Test summary"

        service.evaluate_article = fake_evaluate
        service.generate_summary = fake_generate_summary

        articles = [make_article(title=f"Article {i}") for i in range(5)]
        result = await service.evaluate_batch(articles)

        # All articles should be returned
        assert len(result) == 5
        
        # Check that completion log contains success and failure counts
        info_logs = [record for record in caplog.records if record.levelname == "INFO"]
        completion_log = [log for log in info_logs if "Batch evaluation complete" in log.message]
        
        assert len(completion_log) > 0
        log_message = completion_log[0].message
        
        # Verify counts are logged
        assert "3 successful" in log_message  # 3 successful tinkering_index evaluations
        assert "2 failed" in log_message      # 2 failed tinkering_index evaluations
        assert "4 successful" in log_message  # 4 successful summaries
        assert "1 failed" in log_message      # 1 failed summary

    @pytest.mark.asyncio
    async def test_continues_processing_after_failure(self):
        """evaluate_batch continues processing remaining articles after a failure."""
        service = LLMService.__new__(LLMService)

        call_count = 0
        evaluated_titles = []

        async def fake_evaluate(article):
            nonlocal call_count
            call_count += 1
            evaluated_titles.append(article.title)
            
            # Fail the second article
            if call_count == 2:
                raise Exception("API error")
            
            return AIAnalysis(
                is_hardcore=True,
                reason="reason",
                actionable_takeaway="",
                tinkering_index=3,
            )

        async def fake_generate_summary(article):
            return "Test summary"

        service.evaluate_article = fake_evaluate
        service.generate_summary = fake_generate_summary

        articles = [make_article(title=f"Article {i}") for i in range(5)]
        result = await service.evaluate_batch(articles)

        # All 5 articles should have been attempted
        assert len(evaluated_titles) == 5
        assert len(result) == 5

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

        async def fake_generate_summary(article):
            return "Test summary"

        service.evaluate_article = fake_evaluate
        service.generate_summary = fake_generate_summary

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

        async def fake_generate_summary(article):
            return "Test summary"

        service.evaluate_article = fake_evaluate
        service.generate_summary = fake_generate_summary
        
        articles = [make_article(title=f"Article {i}") for i in range(5)]
        await service.evaluate_batch(articles)

        assert sorted(evaluated_titles) == sorted(a.title for a in articles)

    @pytest.mark.asyncio
    async def test_only_processes_null_tinkering_index(self):
        """evaluate_batch only processes tinkering_index when it's NULL."""
        service = LLMService.__new__(LLMService)
        
        evaluate_called = []
        summary_called = []

        async def fake_evaluate(article):
            evaluate_called.append(article.title)
            return AIAnalysis(is_hardcore=True, reason="r", actionable_takeaway="", tinkering_index=3)

        async def fake_generate_summary(article):
            summary_called.append(article.title)
            return "Test summary"

        service.evaluate_article = fake_evaluate
        service.generate_summary = fake_generate_summary

        # Create articles with different states
        article1 = make_article(title="Article 1")  # Both NULL
        article2 = make_article(title="Article 2")
        article2.tinkering_index = 4  # tinkering_index already set
        
        articles = [article1, article2]
        result = await service.evaluate_batch(articles)

        # evaluate_article should only be called for article1
        assert "Article 1" in evaluate_called
        assert "Article 2" not in evaluate_called
        
        # generate_summary should be called for both
        assert "Article 1" in summary_called
        assert "Article 2" in summary_called

    @pytest.mark.asyncio
    async def test_only_processes_null_ai_summary(self):
        """evaluate_batch only processes ai_summary when it's NULL."""
        service = LLMService.__new__(LLMService)
        
        evaluate_called = []
        summary_called = []

        async def fake_evaluate(article):
            evaluate_called.append(article.title)
            return AIAnalysis(is_hardcore=True, reason="r", actionable_takeaway="", tinkering_index=3)

        async def fake_generate_summary(article):
            summary_called.append(article.title)
            return "Test summary"

        service.evaluate_article = fake_evaluate
        service.generate_summary = fake_generate_summary

        # Create articles with different states
        article1 = make_article(title="Article 1")  # Both NULL
        article2 = make_article(title="Article 2")
        article2.ai_summary = "Existing summary"  # ai_summary already set
        
        articles = [article1, article2]
        result = await service.evaluate_batch(articles)

        # evaluate_article should be called for both
        assert "Article 1" in evaluate_called
        assert "Article 2" in evaluate_called
        
        # generate_summary should only be called for article1
        assert "Article 1" in summary_called
        assert "Article 2" not in summary_called
        
        # article2 should keep its existing summary
        assert result[1].ai_summary == "Existing summary"

    @pytest.mark.asyncio
    async def test_skips_processing_when_both_fields_exist(self):
        """evaluate_batch skips processing when both tinkering_index and ai_summary exist."""
        service = LLMService.__new__(LLMService)
        
        evaluate_called = []
        summary_called = []

        async def fake_evaluate(article):
            evaluate_called.append(article.title)
            return AIAnalysis(is_hardcore=True, reason="r", actionable_takeaway="", tinkering_index=3)

        async def fake_generate_summary(article):
            summary_called.append(article.title)
            return "Test summary"

        service.evaluate_article = fake_evaluate
        service.generate_summary = fake_generate_summary

        # Create article with both fields already set
        article = make_article(title="Complete Article")
        article.tinkering_index = 4
        article.ai_summary = "Existing summary"
        
        result = await service.evaluate_batch([article])

        # Neither method should be called
        assert len(evaluate_called) == 0
        assert len(summary_called) == 0
        
        # Article should keep its existing values
        assert result[0].tinkering_index == 4
        assert result[0].ai_summary == "Existing summary"


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


# ---------------------------------------------------------------------------
# generate_deep_dive
# ---------------------------------------------------------------------------

def make_article_with_analysis(title="Deep Dive Article", category="AI"):
    from uuid import uuid4
    article = ArticleSchema(
        title=title,
        url="https://example.com/deep-dive",
        feed_id=uuid4(),
        feed_name="TestSource",
        category=category,
    )
    article.ai_analysis = AIAnalysis(
        is_hardcore=True,
        reason="Has architecture discussion",
        actionable_takeaway="Deploy with Kubernetes",
        tinkering_index=4,
    )
    return article


class TestGenerateDeepDive:
    @pytest.mark.asyncio
    async def test_returns_string_on_success(self):
        """generate_deep_dive returns a non-empty string when LLM responds."""
        service = LLMService.__new__(LLMService)
        mock_response = MagicMock()
        mock_response.choices[0].message.content = "深度分析內容"
        mock_client = MagicMock()
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
        service.client = mock_client

        result = await service.generate_deep_dive(make_article_with_analysis())

        assert isinstance(result, str)
        assert result == "深度分析內容"

    @pytest.mark.asyncio
    async def test_uses_summarize_model(self):
        """generate_deep_dive uses SUMMARIZE_MODEL (llama-3.3-70b-versatile)."""
        from app.services.llm_service import SUMMARIZE_MODEL

        service = LLMService.__new__(LLMService)
        captured = {}

        async def fake_create(**kwargs):
            captured["model"] = kwargs["model"]
            mock_response = MagicMock()
            mock_response.choices[0].message.content = "分析"
            return mock_response

        mock_client = MagicMock()
        mock_client.chat.completions.create = fake_create
        service.client = mock_client

        await service.generate_deep_dive(make_article_with_analysis())

        assert captured["model"] == SUMMARIZE_MODEL
        assert captured["model"] == "llama-3.3-70b-versatile"

    @pytest.mark.asyncio
    async def test_uses_max_tokens_600(self):
        """generate_deep_dive sets max_tokens=600."""
        service = LLMService.__new__(LLMService)
        captured = {}

        async def fake_create(**kwargs):
            captured["max_tokens"] = kwargs["max_tokens"]
            mock_response = MagicMock()
            mock_response.choices[0].message.content = "分析"
            return mock_response

        mock_client = MagicMock()
        mock_client.chat.completions.create = fake_create
        service.client = mock_client

        await service.generate_deep_dive(make_article_with_analysis())

        assert captured["max_tokens"] == 600

    @pytest.mark.asyncio
    async def test_system_prompt_contains_traditional_chinese(self):
        """generate_deep_dive system prompt requires Traditional Chinese output."""
        service = LLMService.__new__(LLMService)
        captured = {}

        async def fake_create(**kwargs):
            captured["system"] = kwargs["messages"][0]["content"]
            mock_response = MagicMock()
            mock_response.choices[0].message.content = "分析"
            return mock_response

        mock_client = MagicMock()
        mock_client.chat.completions.create = fake_create
        service.client = mock_client

        await service.generate_deep_dive(make_article_with_analysis())

        assert "繁體中文" in captured["system"]

    @pytest.mark.asyncio
    async def test_prompt_includes_title_and_category(self):
        """generate_deep_dive includes title and category in user prompt."""
        service = LLMService.__new__(LLMService)
        captured = {}

        async def fake_create(**kwargs):
            captured["user"] = kwargs["messages"][1]["content"]
            mock_response = MagicMock()
            mock_response.choices[0].message.content = "分析"
            return mock_response

        mock_client = MagicMock()
        mock_client.chat.completions.create = fake_create
        service.client = mock_client

        article = make_article_with_analysis(title="My Title", category="DevOps")
        await service.generate_deep_dive(article)

        assert "My Title" in captured["user"]
        assert "DevOps" in captured["user"]

    @pytest.mark.asyncio
    async def test_handles_article_without_content_preview(self):
        """generate_deep_dive still generates when article has no content_preview field."""
        service = LLMService.__new__(LLMService)
        captured = {}

        async def fake_create(**kwargs):
            captured["user"] = kwargs["messages"][1]["content"]
            mock_response = MagicMock()
            mock_response.choices[0].message.content = "分析"
            return mock_response

        mock_client = MagicMock()
        mock_client.chat.completions.create = fake_create
        service.client = mock_client

        article = make_article_with_analysis(title="Only Title")
        await service.generate_deep_dive(article)

        assert "Only Title" in captured["user"]
        # Ensure the API was still called (no early return)
        assert captured["user"] != ""

    @pytest.mark.asyncio
    async def test_returns_default_string_on_empty_response(self):
        """generate_deep_dive returns default string when LLM returns empty content."""
        service = LLMService.__new__(LLMService)
        mock_response = MagicMock()
        mock_response.choices[0].message.content = ""
        mock_client = MagicMock()
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
        service.client = mock_client

        result = await service.generate_deep_dive(make_article_with_analysis())

        assert result == "無法生成深度摘要內容。"

    @pytest.mark.asyncio
    async def test_returns_default_string_on_none_response(self):
        """generate_deep_dive returns default string when LLM returns None content."""
        service = LLMService.__new__(LLMService)
        mock_response = MagicMock()
        mock_response.choices[0].message.content = None
        mock_client = MagicMock()
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
        service.client = mock_client

        result = await service.generate_deep_dive(make_article_with_analysis())

        assert result == "無法生成深度摘要內容。"

    @pytest.mark.asyncio
    async def test_raises_llm_service_error_on_api_failure(self):
        """generate_deep_dive raises LLMServiceError when API call fails."""
        service = LLMService.__new__(LLMService)
        mock_client = MagicMock()
        mock_client.chat.completions.create = AsyncMock(side_effect=Exception("API error"))
        service.client = mock_client

        with pytest.raises(LLMServiceError):
            await service.generate_deep_dive(make_article_with_analysis())


# ---------------------------------------------------------------------------
# generate_deep_dive — property-based tests (Property 6)
# ---------------------------------------------------------------------------

from hypothesis import given, settings
from hypothesis import strategies as st
from pydantic import HttpUrl


def _make_article_strategy():
    """Strategy to generate random ArticleSchema instances."""
    from uuid import uuid4
    return st.builds(
        ArticleSchema,
        title=st.text(min_size=1, max_size=100),
        url=st.just("https://example.com/article"),
        feed_id=st.just(uuid4()),
        feed_name=st.text(min_size=1, max_size=50),
        category=st.text(min_size=1, max_size=50),
        published_at=st.none(),
        ai_analysis=st.none(),
    )


class TestGenerateDeepDiveProperty:
    # Feature: discord-interaction-enhancement, Property 6: generate_deep_dive 的 prompt 包含文章關鍵欄位
    # Validates: Requirements 5.2, 5.4

    @given(article=_make_article_strategy())
    @settings(max_examples=5)
    def test_prompt_always_contains_title(self, article):
        """Property 6: user prompt always contains the article title."""
        import asyncio

        service = LLMService.__new__(LLMService)
        captured = {}

        async def fake_create(**kwargs):
            captured["user"] = kwargs["messages"][1]["content"]
            mock_response = MagicMock()
            mock_response.choices[0].message.content = "分析"
            return mock_response

        mock_client = MagicMock()
        mock_client.chat.completions.create = fake_create
        service.client = mock_client

        asyncio.get_event_loop().run_until_complete(service.generate_deep_dive(article))

        assert article.title in captured["user"]


# ---------------------------------------------------------------------------
# generate_reading_recommendation
# ---------------------------------------------------------------------------

class TestGenerateReadingRecommendation:
    @pytest.mark.asyncio
    async def test_returns_string_on_success(self):
        """generate_reading_recommendation returns a non-empty string when LLM responds."""
        service = LLMService.__new__(LLMService)
        mock_response = MagicMock()
        mock_response.choices[0].message.content = "推薦摘要內容"
        mock_client = MagicMock()
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
        service.client = mock_client

        result = await service.generate_reading_recommendation(
            titles=["文章一", "文章二"],
            categories=["AI", "DevOps"],
        )

        assert isinstance(result, str)
        assert result == "推薦摘要內容"

    @pytest.mark.asyncio
    async def test_raises_llm_service_error_on_api_failure(self):
        """generate_reading_recommendation raises LLMServiceError when API call fails."""
        service = LLMService.__new__(LLMService)
        mock_client = MagicMock()
        mock_client.chat.completions.create = AsyncMock(side_effect=Exception("API error"))
        service.client = mock_client

        with pytest.raises(LLMServiceError):
            await service.generate_reading_recommendation(
                titles=["文章一"],
                categories=["AI"],
            )

    @pytest.mark.asyncio
    async def test_raises_llm_service_error_on_empty_response(self):
        """generate_reading_recommendation raises LLMServiceError when LLM returns empty content."""
        service = LLMService.__new__(LLMService)
        mock_response = MagicMock()
        mock_response.choices[0].message.content = ""
        mock_client = MagicMock()
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
        service.client = mock_client

        with pytest.raises(LLMServiceError):
            await service.generate_reading_recommendation(
                titles=["文章一"],
                categories=["AI"],
            )

    @pytest.mark.asyncio
    async def test_prompt_includes_titles_and_categories(self):
        """generate_reading_recommendation includes titles and categories in the user prompt."""
        service = LLMService.__new__(LLMService)
        captured = {}

        async def fake_create(**kwargs):
            captured["user"] = kwargs["messages"][1]["content"]
            mock_response = MagicMock()
            mock_response.choices[0].message.content = "摘要"
            return mock_response

        mock_client = MagicMock()
        mock_client.chat.completions.create = fake_create
        service.client = mock_client

        await service.generate_reading_recommendation(
            titles=["Kubernetes 深度解析", "Rust 入門"],
            categories=["DevOps", "Systems"],
        )

        assert "Kubernetes 深度解析" in captured["user"]
        assert "Rust 入門" in captured["user"]
        assert "DevOps" in captured["user"]
        assert "Systems" in captured["user"]

    @pytest.mark.asyncio
    async def test_system_prompt_requires_traditional_chinese_and_500_char_limit(self):
        """generate_reading_recommendation system prompt requires 繁體中文 and 500 char limit."""
        service = LLMService.__new__(LLMService)
        captured = {}

        async def fake_create(**kwargs):
            captured["system"] = kwargs["messages"][0]["content"]
            mock_response = MagicMock()
            mock_response.choices[0].message.content = "摘要"
            return mock_response

        mock_client = MagicMock()
        mock_client.chat.completions.create = fake_create
        service.client = mock_client

        await service.generate_reading_recommendation(
            titles=["文章一"],
            categories=["AI"],
        )

        assert "繁體中文" in captured["system"]
        assert "500" in captured["system"]

    @pytest.mark.asyncio
    async def test_uses_summarize_model(self):
        """generate_reading_recommendation uses SUMMARIZE_MODEL."""
        from app.services.llm_service import SUMMARIZE_MODEL

        service = LLMService.__new__(LLMService)
        captured = {}

        async def fake_create(**kwargs):
            captured["model"] = kwargs["model"]
            mock_response = MagicMock()
            mock_response.choices[0].message.content = "摘要"
            return mock_response

        mock_client = MagicMock()
        mock_client.chat.completions.create = fake_create
        service.client = mock_client

        await service.generate_reading_recommendation(
            titles=["文章一"],
            categories=["AI"],
        )

        assert captured["model"] == SUMMARIZE_MODEL
