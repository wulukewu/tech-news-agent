"""
Unit tests for LLMService.generate_digest_intro
Covers: fallback on LLM failure (Requirement 4.4)
"""
import pytest
from unittest.mock import AsyncMock, MagicMock

from app.schemas.article import ArticleSchema, AIAnalysis
from app.services.llm_service import LLMService, SUMMARIZE_MODEL

FALLBACK_TEXT = "本週精選技術文章，請展開各項目查看詳情。"


def make_hardcore_article(title="Hardcore Article", tinkering_index=3):
    article = ArticleSchema(
        title=title,
        url="https://example.com/article",
        content_preview="Some technical content preview",
        source_category="AI",
        source_name="TestSource",
    )
    article.ai_analysis = AIAnalysis(
        is_hardcore=True,
        reason="Has code and architecture discussion",
        actionable_takeaway="Deploy with Docker",
        tinkering_index=tinkering_index,
    )
    return article


class TestGenerateDigestIntroFallback:
    """Tests for generate_digest_intro failure degradation (Requirement 4.4)."""

    @pytest.mark.asyncio
    async def test_returns_fallback_on_api_exception(self):
        """When LLM call raises an exception, returns fallback text without raising."""
        service = LLMService.__new__(LLMService)
        mock_client = MagicMock()
        mock_client.chat.completions.create = AsyncMock(side_effect=Exception("API timeout"))
        service.client = mock_client

        result = await service.generate_digest_intro([make_hardcore_article()])

        assert result == FALLBACK_TEXT

    @pytest.mark.asyncio
    async def test_does_not_raise_on_api_exception(self):
        """generate_digest_intro must not propagate exceptions to the caller."""
        service = LLMService.__new__(LLMService)
        mock_client = MagicMock()
        mock_client.chat.completions.create = AsyncMock(side_effect=RuntimeError("network error"))
        service.client = mock_client

        # Should not raise
        try:
            await service.generate_digest_intro([make_hardcore_article()])
        except Exception as exc:
            pytest.fail(f"generate_digest_intro raised unexpectedly: {exc}")

    @pytest.mark.asyncio
    async def test_returns_fallback_on_empty_response(self):
        """When LLM returns empty content, returns fallback text."""
        service = LLMService.__new__(LLMService)
        mock_response = MagicMock()
        mock_response.choices[0].message.content = ""
        mock_client = MagicMock()
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
        service.client = mock_client

        result = await service.generate_digest_intro([make_hardcore_article()])

        assert result == FALLBACK_TEXT

    @pytest.mark.asyncio
    async def test_returns_fallback_on_none_response(self):
        """When LLM returns None content, returns fallback text."""
        service = LLMService.__new__(LLMService)
        mock_response = MagicMock()
        mock_response.choices[0].message.content = None
        mock_client = MagicMock()
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
        service.client = mock_client

        result = await service.generate_digest_intro([make_hardcore_article()])

        assert result == FALLBACK_TEXT

    @pytest.mark.asyncio
    async def test_returns_llm_content_on_success(self):
        """When LLM responds successfully, returns the LLM-generated content."""
        service = LLMService.__new__(LLMService)
        expected = "本週技術圈最熱門的話題是 AI 與 Rust 的完美結合！"
        mock_response = MagicMock()
        mock_response.choices[0].message.content = expected
        mock_client = MagicMock()
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
        service.client = mock_client

        result = await service.generate_digest_intro([make_hardcore_article()])

        assert result == expected
        assert result != FALLBACK_TEXT

    @pytest.mark.asyncio
    async def test_uses_summarize_model(self):
        """generate_digest_intro uses SUMMARIZE_MODEL."""
        service = LLMService.__new__(LLMService)
        captured = {}

        async def fake_create(**kwargs):
            captured["model"] = kwargs["model"]
            mock_response = MagicMock()
            mock_response.choices[0].message.content = "前言內容"
            return mock_response

        mock_client = MagicMock()
        mock_client.chat.completions.create = fake_create
        service.client = mock_client

        await service.generate_digest_intro([make_hardcore_article()])

        assert captured["model"] == SUMMARIZE_MODEL

    @pytest.mark.asyncio
    async def test_returns_fallback_for_empty_article_list(self):
        """When article list is empty and LLM fails, still returns fallback text."""
        service = LLMService.__new__(LLMService)
        mock_client = MagicMock()
        mock_client.chat.completions.create = AsyncMock(side_effect=Exception("error"))
        service.client = mock_client

        result = await service.generate_digest_intro([])

        assert result == FALLBACK_TEXT

    @pytest.mark.asyncio
    async def test_fallback_text_is_correct_string(self):
        """Fallback text matches the exact required default string."""
        service = LLMService.__new__(LLMService)
        mock_client = MagicMock()
        mock_client.chat.completions.create = AsyncMock(side_effect=ValueError("bad input"))
        service.client = mock_client

        result = await service.generate_digest_intro([make_hardcore_article()])

        assert result == "本週精選技術文章，請展開各項目查看詳情。"
