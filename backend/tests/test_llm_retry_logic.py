"""
Unit tests for LLM Service retry logic
Tests the exponential backoff retry mechanism with Retry-After header support
"""

import asyncio
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

from app.core.exceptions import LLMServiceError
from app.schemas.article import AIAnalysis, ArticleSchema
from app.services.llm_service import MAX_RETRIES, RETRY_DELAYS, LLMService


def make_article(title="Test Article", url="https://example.com/article"):
    return ArticleSchema(
        title=title,
        url=url,
        feed_id=uuid4(),
        feed_name="TestSource",
        category="AI",
    )


class TestRetryLogic:
    @pytest.mark.asyncio
    async def test_succeeds_on_first_attempt(self):
        """Retry logic succeeds immediately when API call works on first attempt."""
        service = LLMService.__new__(LLMService)

        call_count = 0

        async def mock_api_call():
            nonlocal call_count
            call_count += 1
            return "success"

        result = await service._call_api_with_retry(mock_api_call, "test_context")

        assert result == "success"
        assert call_count == 1  # Only called once

    @pytest.mark.asyncio
    async def test_retries_on_transient_error(self):
        """Retry logic retries on transient errors and eventually succeeds."""
        service = LLMService.__new__(LLMService)

        call_count = 0

        async def mock_api_call():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise Exception("Transient error")
            return "success"

        result = await service._call_api_with_retry(mock_api_call, "test_context")

        assert result == "success"
        assert call_count == 2  # Called twice (initial + 1 retry)

    @pytest.mark.asyncio
    async def test_exhausts_retries_and_raises(self):
        """Retry logic exhausts all retries and raises the last exception."""
        service = LLMService.__new__(LLMService)

        call_count = 0

        async def mock_api_call():
            nonlocal call_count
            call_count += 1
            raise Exception("Persistent error")

        with pytest.raises(Exception, match="Persistent error"):
            await service._call_api_with_retry(mock_api_call, "test_context")

        assert call_count == MAX_RETRIES + 1  # Initial + 2 retries = 3 total

    @pytest.mark.asyncio
    async def test_uses_exponential_backoff_delays(self):
        """Retry logic uses exponential backoff delays (2s, 4s)."""
        service = LLMService.__new__(LLMService)

        delays_used = []
        original_sleep = asyncio.sleep

        async def mock_sleep(delay):
            delays_used.append(delay)
            # Don't actually sleep in tests
            await original_sleep(0)

        call_count = 0

        async def mock_api_call():
            nonlocal call_count
            call_count += 1
            raise Exception("Error")

        with patch("asyncio.sleep", side_effect=mock_sleep), pytest.raises(Exception):
            await service._call_api_with_retry(mock_api_call, "test_context")

        assert delays_used == RETRY_DELAYS  # [2, 4]

    @pytest.mark.asyncio
    async def test_respects_retry_after_header(self):
        """Retry logic respects Retry-After header from API response."""
        service = LLMService.__new__(LLMService)

        delays_used = []
        original_sleep = asyncio.sleep

        async def mock_sleep(delay):
            delays_used.append(delay)
            await original_sleep(0)

        call_count = 0

        async def mock_api_call():
            nonlocal call_count
            call_count += 1

            # Create exception with Retry-After header
            error = Exception("Rate limited")
            error.response = MagicMock()
            error.response.headers = {"Retry-After": "10"}
            raise error

        with patch("asyncio.sleep", side_effect=mock_sleep), pytest.raises(Exception):
            await service._call_api_with_retry(mock_api_call, "test_context")

        # Should use Retry-After values instead of exponential backoff
        assert delays_used == [10.0, 10.0]

    @pytest.mark.asyncio
    async def test_logs_retry_attempts(self, caplog):
        """Retry logic logs each retry attempt."""
        import logging

        caplog.set_level(logging.INFO)

        service = LLMService.__new__(LLMService)

        call_count = 0

        async def mock_api_call():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise Exception("Error")
            return "success"

        with patch("asyncio.sleep", return_value=asyncio.sleep(0)):
            result = await service._call_api_with_retry(mock_api_call, "test_context")

        assert result == "success"

        # Check that retry attempts were logged
        assert any(
            "Retry attempt 1/2 for test_context" in record.message for record in caplog.records
        )
        assert any(
            "Retry attempt 2/2 for test_context" in record.message for record in caplog.records
        )

    @pytest.mark.asyncio
    async def test_logs_final_error_on_exhaustion(self, caplog):
        """Retry logic logs final error when all retries are exhausted."""
        import logging

        caplog.set_level(logging.ERROR)

        service = LLMService.__new__(LLMService)

        async def mock_api_call():
            raise Exception("Persistent error")

        with patch("asyncio.sleep", return_value=asyncio.sleep(0)):
            with pytest.raises(Exception):
                await service._call_api_with_retry(mock_api_call, "test_context")

        # Check that final error was logged
        assert any(
            "All retry attempts exhausted for test_context" in record.message
            for record in caplog.records
        )

    @pytest.mark.asyncio
    async def test_logs_rate_limit_with_retry_after(self, caplog):
        """Retry logic logs rate limit events with Retry-After header."""
        import logging

        caplog.set_level(logging.WARNING)

        service = LLMService.__new__(LLMService)

        call_count = 0

        async def mock_api_call():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                error = Exception("Rate limited")
                error.response = MagicMock()
                error.response.headers = {"Retry-After": "5"}
                raise error
            return "success"

        with patch("asyncio.sleep", return_value=asyncio.sleep(0)):
            result = await service._call_api_with_retry(mock_api_call, "test_context")

        assert result == "success"

        # Check that rate limit was logged
        assert any("Rate limited for test_context" in record.message for record in caplog.records)
        assert any("Retry-After header indicates 5" in record.message for record in caplog.records)


class TestEvaluateArticleWithRetry:
    @pytest.mark.asyncio
    async def test_evaluate_article_retries_on_api_error(self):
        """evaluate_article uses retry logic and succeeds after transient error."""
        service = LLMService.__new__(LLMService)

        call_count = 0

        async def mock_create(**kwargs):
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise Exception("Transient API error")

            mock_response = MagicMock()
            mock_response.choices[0].message.content = (
                '{"is_hardcore": true, "reason": "Has code", '
                '"actionable_takeaway": "Use it", "tinkering_index": 3}'
            )
            return mock_response

        mock_client = MagicMock()
        mock_client.chat.completions.create = mock_create
        service.client = mock_client

        with patch("asyncio.sleep", return_value=asyncio.sleep(0)):
            result = await service.evaluate_article(make_article())

        assert isinstance(result, AIAnalysis)
        assert result.is_hardcore is True
        assert call_count == 2  # Initial + 1 retry

    @pytest.mark.asyncio
    async def test_evaluate_article_returns_fallback_after_all_retries_fail(self):
        """evaluate_article returns fallback when all retries are exhausted."""
        service = LLMService.__new__(LLMService)

        call_count = 0

        async def mock_create(**kwargs):
            nonlocal call_count
            call_count += 1
            raise Exception("Persistent API error")

        mock_client = MagicMock()
        mock_client.chat.completions.create = mock_create
        service.client = mock_client

        with patch("asyncio.sleep", return_value=asyncio.sleep(0)):
            result = await service.evaluate_article(make_article())

        # Should return fallback
        assert result.is_hardcore is False
        assert result.tinkering_index == 0
        assert call_count == MAX_RETRIES + 1  # All retries exhausted


class TestGenerateDeepDiveWithRetry:
    @pytest.mark.asyncio
    async def test_generate_deep_dive_retries_on_api_error(self):
        """generate_deep_dive uses retry logic and succeeds after transient error."""
        from uuid import uuid4

        article = ArticleSchema(
            title="Deep Dive Article",
            url="https://example.com/deep-dive",
            feed_id=uuid4(),
            feed_name="TestSource",
            category="AI",
        )
        article.ai_analysis = AIAnalysis(
            is_hardcore=True,
            reason="Has architecture discussion",
            actionable_takeaway="Deploy with Kubernetes",
            tinkering_index=4,
        )

        service = LLMService.__new__(LLMService)

        call_count = 0

        async def mock_create(**kwargs):
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise Exception("Transient API error")

            mock_response = MagicMock()
            mock_response.choices[0].message.content = "深度分析內容"
            return mock_response

        mock_client = MagicMock()
        mock_client.chat.completions.create = mock_create
        service.client = mock_client

        with patch("asyncio.sleep", return_value=asyncio.sleep(0)):
            result = await service.generate_deep_dive(article)

        assert result == "深度分析內容"
        assert call_count == 2  # Initial + 1 retry

    @pytest.mark.asyncio
    async def test_generate_deep_dive_raises_after_all_retries_fail(self):
        """generate_deep_dive raises LLMServiceError when all retries are exhausted."""
        from uuid import uuid4

        article = ArticleSchema(
            title="Deep Dive Article",
            url="https://example.com/deep-dive",
            feed_id=uuid4(),
            feed_name="TestSource",
            category="AI",
        )

        service = LLMService.__new__(LLMService)

        async def mock_create(**kwargs):
            raise Exception("Persistent API error")

        mock_client = MagicMock()
        mock_client.chat.completions.create = mock_create
        service.client = mock_client

        with patch("asyncio.sleep", return_value=asyncio.sleep(0)):
            with pytest.raises(LLMServiceError):
                await service.generate_deep_dive(article)


class TestTimeoutConfiguration:
    @pytest.mark.asyncio
    async def test_client_has_30_second_timeout(self):
        """LLMService client is configured with 30 second timeout."""
        from app.services.llm_service import API_TIMEOUT

        service = LLMService()

        assert API_TIMEOUT == 30
        assert service.client.timeout == 30
