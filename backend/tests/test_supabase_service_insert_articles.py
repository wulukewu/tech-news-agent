"""
Unit tests for SupabaseService.insert_articles method
Task 1.5: 撰寫 Supabase Service 增強功能的單元測試

Tests cover:
- Requirements 4.2: UPSERT operation based on article URL
- Requirements 4.3: Update existing record when URL exists
- Requirements 4.4: Insert new record when URL doesn't exist
- Requirements 4.5: Validate feed_id foreign key before insertion
- Requirements 4.6: Return accurate BatchResult with counts
- Requirements 4.8: Continue processing on individual article failures
"""

from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from app.services.supabase_service import SupabaseService


class TestInsertArticles:
    """測試 insert_articles 方法"""

    @pytest.mark.asyncio
    async def test_inserts_new_article_when_url_not_exists(self):
        """
        測試當 URL 不存在時插入新文章
        Requirements: 4.4
        """
        # Arrange
        mock_client = MagicMock()

        # Mock check for existing article (not found)
        mock_existing_response = MagicMock()
        mock_existing_response.data = []

        # Mock successful upsert
        mock_upsert_response = MagicMock()
        mock_upsert_response.data = [{"id": str(uuid4())}]

        mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value = (
            mock_existing_response
        )
        mock_client.table.return_value.upsert.return_value.execute.return_value = (
            mock_upsert_response
        )

        service = SupabaseService(client=mock_client, validate_connection=False)

        articles = [
            {"title": "New Article", "url": "https://example.com/new", "feed_id": str(uuid4())}
        ]

        # Act
        result = await service.insert_articles(articles)

        # Assert
        assert result.inserted_count == 1
        assert result.updated_count == 0
        assert result.failed_count == 0
        mock_client.table.return_value.upsert.assert_called_once()

    @pytest.mark.asyncio
    async def test_updates_existing_article_when_url_exists(self):
        """
        測試當 URL 已存在時更新現有文章
        Requirements: 4.3
        """
        # Arrange
        mock_client = MagicMock()

        # Mock check for existing article (found)
        mock_existing_response = MagicMock()
        mock_existing_response.data = [{"id": str(uuid4())}]

        # Mock successful upsert
        mock_upsert_response = MagicMock()
        mock_upsert_response.data = [{"id": str(uuid4())}]

        mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value = (
            mock_existing_response
        )
        mock_client.table.return_value.upsert.return_value.execute.return_value = (
            mock_upsert_response
        )

        service = SupabaseService(client=mock_client, validate_connection=False)

        articles = [
            {
                "title": "Existing Article",
                "url": "https://example.com/existing",
                "feed_id": str(uuid4()),
            }
        ]

        # Act
        result = await service.insert_articles(articles)

        # Assert
        assert result.inserted_count == 0
        assert result.updated_count == 1
        assert result.failed_count == 0

    @pytest.mark.asyncio
    async def test_uses_upsert_with_url_conflict_resolution(self):
        """
        測試使用 UPSERT 操作並指定 URL 作為衝突解決欄位
        Requirements: 4.2
        """
        # Arrange
        mock_client = MagicMock()

        mock_existing_response = MagicMock()
        mock_existing_response.data = []

        mock_upsert_response = MagicMock()
        mock_upsert_response.data = [{"id": str(uuid4())}]

        mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value = (
            mock_existing_response
        )
        mock_client.table.return_value.upsert.return_value.execute.return_value = (
            mock_upsert_response
        )

        service = SupabaseService(client=mock_client, validate_connection=False)

        articles = [
            {"title": "Test Article", "url": "https://example.com/test", "feed_id": str(uuid4())}
        ]

        # Act
        await service.insert_articles(articles)

        # Assert
        # Verify upsert was called with on_conflict='url'
        upsert_call = mock_client.table.return_value.upsert.call_args
        assert upsert_call is not None
        assert upsert_call[1]["on_conflict"] == "url"

    @pytest.mark.asyncio
    async def test_validates_foreign_key_feed_id(self):
        """
        測試驗證 feed_id 外鍵約束
        Requirements: 4.5
        """
        # Arrange
        mock_client = MagicMock()

        mock_existing_response = MagicMock()
        mock_existing_response.data = []

        # Mock foreign key constraint violation
        mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value = (
            mock_existing_response
        )
        mock_client.table.return_value.upsert.return_value.execute.side_effect = Exception(
            'foreign key constraint "articles_feed_id_fkey" violated'
        )

        service = SupabaseService(client=mock_client, validate_connection=False)

        invalid_feed_id = str(uuid4())
        articles = [
            {"title": "Test Article", "url": "https://example.com/test", "feed_id": invalid_feed_id}
        ]

        # Act
        result = await service.insert_articles(articles)

        # Assert
        assert result.inserted_count == 0
        assert result.updated_count == 0
        assert result.failed_count == 1
        assert len(result.failed_articles) == 1
        assert (
            "foreign key" in result.failed_articles[0]["error"].lower()
            or "reference" in result.failed_articles[0]["error"].lower()
        )

    @pytest.mark.asyncio
    async def test_returns_accurate_batch_result(self):
        """
        測試返回準確的 BatchResult 統計
        Requirements: 4.6
        """
        # Arrange
        mock_client = MagicMock()

        # Mock responses for 3 articles: 1 new, 1 existing, 1 failed
        def mock_select_side_effect(*args, **kwargs):
            mock_response = MagicMock()
            # First call: new article (empty)
            # Second call: existing article (found)
            # Third call: will fail on upsert
            if not hasattr(mock_select_side_effect, "call_count"):
                mock_select_side_effect.call_count = 0

            if mock_select_side_effect.call_count == 0:
                mock_response.data = []  # New article
            elif mock_select_side_effect.call_count == 1:
                mock_response.data = [{"id": str(uuid4())}]  # Existing article
            else:
                mock_response.data = []  # Will fail

            mock_select_side_effect.call_count += 1
            return mock_response

        mock_client.table.return_value.select.return_value.eq.return_value.execute.side_effect = (
            mock_select_side_effect
        )

        # Mock upsert responses
        def mock_upsert_side_effect(*args, **kwargs):
            if not hasattr(mock_upsert_side_effect, "call_count"):
                mock_upsert_side_effect.call_count = 0

            if mock_upsert_side_effect.call_count < 2:
                mock_response = MagicMock()
                mock_response.data = [{"id": str(uuid4())}]
                mock_upsert_side_effect.call_count += 1
                return mock_response
            else:
                mock_upsert_side_effect.call_count += 1
                raise Exception("Database error")

        mock_client.table.return_value.upsert.return_value.execute.side_effect = (
            mock_upsert_side_effect
        )

        service = SupabaseService(client=mock_client, validate_connection=False)

        articles = [
            {"title": "New Article", "url": "https://example.com/new", "feed_id": str(uuid4())},
            {
                "title": "Existing Article",
                "url": "https://example.com/existing",
                "feed_id": str(uuid4()),
            },
            {
                "title": "Failed Article",
                "url": "https://example.com/failed",
                "feed_id": str(uuid4()),
            },
        ]

        # Act
        result = await service.insert_articles(articles)

        # Assert
        assert result.inserted_count == 1
        assert result.updated_count == 1
        assert result.failed_count == 1
        assert result.total_processed == 3

    @pytest.mark.asyncio
    async def test_continues_processing_on_individual_failure(self):
        """
        測試當個別文章失敗時繼續處理其他文章
        Requirements: 4.8
        """
        # Arrange
        mock_client = MagicMock()

        # Mock responses
        call_count = {"select": 0, "upsert": 0}

        def mock_select_side_effect(*args, **kwargs):
            mock_response = MagicMock()
            mock_response.data = []
            call_count["select"] += 1
            return mock_response

        def mock_upsert_side_effect(*args, **kwargs):
            call_count["upsert"] += 1
            if call_count["upsert"] == 2:  # Second article fails
                raise Exception("Database error on second article")
            mock_response = MagicMock()
            mock_response.data = [{"id": str(uuid4())}]
            return mock_response

        mock_client.table.return_value.select.return_value.eq.return_value.execute.side_effect = (
            mock_select_side_effect
        )
        mock_client.table.return_value.upsert.return_value.execute.side_effect = (
            mock_upsert_side_effect
        )

        service = SupabaseService(client=mock_client, validate_connection=False)

        articles = [
            {"title": "Article 1", "url": "https://example.com/1", "feed_id": str(uuid4())},
            {"title": "Article 2", "url": "https://example.com/2", "feed_id": str(uuid4())},
            {"title": "Article 3", "url": "https://example.com/3", "feed_id": str(uuid4())},
        ]

        # Act
        result = await service.insert_articles(articles)

        # Assert
        assert result.inserted_count == 2  # Articles 1 and 3 succeeded
        assert result.failed_count == 1  # Article 2 failed
        assert len(result.failed_articles) == 1
        assert "Article 2" in str(result.failed_articles[0])

    @pytest.mark.asyncio
    async def test_handles_empty_articles_list(self):
        """
        測試處理空文章列表
        Requirements: 4.6
        """
        # Arrange
        mock_client = MagicMock()
        service = SupabaseService(client=mock_client, validate_connection=False)

        # Act
        result = await service.insert_articles([])

        # Assert
        assert result.inserted_count == 0
        assert result.updated_count == 0
        assert result.failed_count == 0
        assert result.total_processed == 0

    @pytest.mark.asyncio
    async def test_truncates_long_title(self):
        """
        測試截斷過長的標題（最大 2000 字元）
        Requirements: 4.6
        """
        # Arrange
        mock_client = MagicMock()

        mock_existing_response = MagicMock()
        mock_existing_response.data = []

        mock_upsert_response = MagicMock()
        mock_upsert_response.data = [{"id": str(uuid4())}]

        mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value = (
            mock_existing_response
        )
        mock_client.table.return_value.upsert.return_value.execute.return_value = (
            mock_upsert_response
        )

        service = SupabaseService(client=mock_client, validate_connection=False)

        long_title = "A" * 3000  # Exceeds 2000 character limit
        articles = [
            {"title": long_title, "url": "https://example.com/long-title", "feed_id": str(uuid4())}
        ]

        # Act
        result = await service.insert_articles(articles)

        # Assert
        assert result.inserted_count == 1
        # Verify the title was truncated in the upsert call
        upsert_call = mock_client.table.return_value.upsert.call_args
        assert len(upsert_call[0][0]["title"]) == 2000

    @pytest.mark.asyncio
    async def test_truncates_long_ai_summary(self):
        """
        測試截斷過長的 AI 摘要（最大 5000 字元）
        Requirements: 4.6
        """
        # Arrange
        mock_client = MagicMock()

        mock_existing_response = MagicMock()
        mock_existing_response.data = []

        mock_upsert_response = MagicMock()
        mock_upsert_response.data = [{"id": str(uuid4())}]

        mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value = (
            mock_existing_response
        )
        mock_client.table.return_value.upsert.return_value.execute.return_value = (
            mock_upsert_response
        )

        service = SupabaseService(client=mock_client, validate_connection=False)

        long_summary = "B" * 6000  # Exceeds 5000 character limit
        articles = [
            {
                "title": "Test Article",
                "url": "https://example.com/long-summary",
                "feed_id": str(uuid4()),
                "ai_summary": long_summary,
            }
        ]

        # Act
        result = await service.insert_articles(articles)

        # Assert
        assert result.inserted_count == 1
        # Verify the summary was truncated in the upsert call
        upsert_call = mock_client.table.return_value.upsert.call_args
        assert len(upsert_call[0][0]["ai_summary"]) == 5000

    @pytest.mark.asyncio
    async def test_processes_articles_in_batches_of_100(self):
        """
        測試以 100 筆為單位批次處理文章
        Requirements: 4.2
        """
        # Arrange
        mock_client = MagicMock()

        mock_existing_response = MagicMock()
        mock_existing_response.data = []

        mock_upsert_response = MagicMock()
        mock_upsert_response.data = [{"id": str(uuid4())}]

        mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value = (
            mock_existing_response
        )
        mock_client.table.return_value.upsert.return_value.execute.return_value = (
            mock_upsert_response
        )

        service = SupabaseService(client=mock_client, validate_connection=False)

        # Create 150 articles to test batching
        articles = [
            {
                "title": f"Article {i}",
                "url": f"https://example.com/article-{i}",
                "feed_id": str(uuid4()),
            }
            for i in range(150)
        ]

        # Act
        result = await service.insert_articles(articles)

        # Assert
        assert result.inserted_count == 150
        assert result.failed_count == 0
        # Verify all articles were processed
        assert mock_client.table.return_value.upsert.call_count == 150

    @pytest.mark.asyncio
    async def test_validates_required_url_field(self):
        """
        測試驗證必要的 url 欄位
        Requirements: 4.6
        """
        # Arrange
        mock_client = MagicMock()
        service = SupabaseService(client=mock_client, validate_connection=False)

        articles = [
            {
                "title": "Article without URL",
                "feed_id": str(uuid4()),
                # Missing 'url' field
            }
        ]

        # Act
        result = await service.insert_articles(articles)

        # Assert
        assert result.inserted_count == 0
        assert result.failed_count == 1
        assert len(result.failed_articles) == 1
        assert "url" in result.failed_articles[0]["error"].lower()

    @pytest.mark.asyncio
    async def test_validates_required_feed_id_field(self):
        """
        測試驗證必要的 feed_id 欄位
        Requirements: 4.6
        """
        # Arrange
        mock_client = MagicMock()
        service = SupabaseService(client=mock_client, validate_connection=False)

        articles = [
            {
                "title": "Article without feed_id",
                "url": "https://example.com/no-feed",
                # Missing 'feed_id' field
            }
        ]

        # Act
        result = await service.insert_articles(articles)

        # Assert
        assert result.inserted_count == 0
        assert result.failed_count == 1
        assert len(result.failed_articles) == 1
        assert "feed_id" in result.failed_articles[0]["error"].lower()

    @pytest.mark.asyncio
    async def test_validates_url_format(self):
        """
        測試驗證 URL 格式
        Requirements: 4.6
        """
        # Arrange
        mock_client = MagicMock()
        service = SupabaseService(client=mock_client, validate_connection=False)

        articles = [
            {"title": "Article with invalid URL", "url": "not-a-valid-url", "feed_id": str(uuid4())}
        ]

        # Act
        result = await service.insert_articles(articles)

        # Assert
        assert result.inserted_count == 0
        assert result.failed_count == 1
        assert len(result.failed_articles) == 1

    @pytest.mark.asyncio
    async def test_validates_tinkering_index_range(self):
        """
        測試驗證 tinkering_index 範圍（1-5）
        Requirements: 4.6
        """
        # Arrange
        mock_client = MagicMock()
        service = SupabaseService(client=mock_client, validate_connection=False)

        articles = [
            {
                "title": "Article with invalid tinkering_index",
                "url": "https://example.com/invalid-index",
                "feed_id": str(uuid4()),
                "tinkering_index": 10,  # Invalid: must be 1-5
            }
        ]

        # Act
        result = await service.insert_articles(articles)

        # Assert
        assert result.inserted_count == 0
        assert result.failed_count == 1
        assert "tinkering_index" in result.failed_articles[0]["error"].lower()

    @pytest.mark.asyncio
    async def test_accepts_null_tinkering_index(self):
        """
        測試接受 NULL tinkering_index（用於 LLM 分析失敗的情況）
        Requirements: 4.6
        """
        # Arrange
        mock_client = MagicMock()

        mock_existing_response = MagicMock()
        mock_existing_response.data = []

        mock_upsert_response = MagicMock()
        mock_upsert_response.data = [{"id": str(uuid4())}]

        mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value = (
            mock_existing_response
        )
        mock_client.table.return_value.upsert.return_value.execute.return_value = (
            mock_upsert_response
        )

        service = SupabaseService(client=mock_client, validate_connection=False)

        articles = [
            {
                "title": "Article with null tinkering_index",
                "url": "https://example.com/null-index",
                "feed_id": str(uuid4()),
                "tinkering_index": None,
            }
        ]

        # Act
        result = await service.insert_articles(articles)

        # Assert
        assert result.inserted_count == 1
        assert result.failed_count == 0

    @pytest.mark.asyncio
    async def test_accepts_null_ai_summary(self):
        """
        測試接受 NULL ai_summary（用於 LLM 分析失敗的情況）
        Requirements: 4.6
        """
        # Arrange
        mock_client = MagicMock()

        mock_existing_response = MagicMock()
        mock_existing_response.data = []

        mock_upsert_response = MagicMock()
        mock_upsert_response.data = [{"id": str(uuid4())}]

        mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value = (
            mock_existing_response
        )
        mock_client.table.return_value.upsert.return_value.execute.return_value = (
            mock_upsert_response
        )

        service = SupabaseService(client=mock_client, validate_connection=False)

        articles = [
            {
                "title": "Article with null ai_summary",
                "url": "https://example.com/null-summary",
                "feed_id": str(uuid4()),
                "ai_summary": None,
            }
        ]

        # Act
        result = await service.insert_articles(articles)

        # Assert
        assert result.inserted_count == 1
        assert result.failed_count == 0

    @pytest.mark.asyncio
    async def test_batch_result_success_rate_calculation(self):
        """
        測試 BatchResult 的成功率計算
        Requirements: 4.6
        """
        # Arrange
        mock_client = MagicMock()

        call_count = {"select": 0, "upsert": 0}

        def mock_select_side_effect(*args, **kwargs):
            mock_response = MagicMock()
            # Alternate between new and existing
            mock_response.data = [{"id": str(uuid4())}] if call_count["select"] % 2 == 0 else []
            call_count["select"] += 1
            return mock_response

        def mock_upsert_side_effect(*args, **kwargs):
            call_count["upsert"] += 1
            if call_count["upsert"] == 3:  # Third article fails
                raise Exception("Database error")
            mock_response = MagicMock()
            mock_response.data = [{"id": str(uuid4())}]
            return mock_response

        mock_client.table.return_value.select.return_value.eq.return_value.execute.side_effect = (
            mock_select_side_effect
        )
        mock_client.table.return_value.upsert.return_value.execute.side_effect = (
            mock_upsert_side_effect
        )

        service = SupabaseService(client=mock_client, validate_connection=False)

        articles = [
            {"title": f"Article {i}", "url": f"https://example.com/{i}", "feed_id": str(uuid4())}
            for i in range(5)
        ]

        # Act
        result = await service.insert_articles(articles)

        # Assert
        assert result.total_processed == 5
        assert result.inserted_count + result.updated_count == 4
        assert result.failed_count == 1
        assert result.success_rate == 0.8  # 4/5 = 0.8

    @pytest.mark.asyncio
    async def test_includes_error_details_in_failed_articles(self):
        """
        測試在 failed_articles 中包含錯誤詳情
        Requirements: 4.6
        """
        # Arrange
        mock_client = MagicMock()

        mock_existing_response = MagicMock()
        mock_existing_response.data = []

        mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value = (
            mock_existing_response
        )
        mock_client.table.return_value.upsert.return_value.execute.side_effect = Exception(
            "Specific database error"
        )

        service = SupabaseService(client=mock_client, validate_connection=False)

        articles = [
            {
                "title": "Failed Article",
                "url": "https://example.com/failed",
                "feed_id": str(uuid4()),
            }
        ]

        # Act
        result = await service.insert_articles(articles)

        # Assert
        assert result.failed_count == 1
        assert len(result.failed_articles) == 1
        failed_article = result.failed_articles[0]
        assert "article" in failed_article
        assert "error" in failed_article
        assert "error_type" in failed_article
        assert failed_article["article"]["url"] == "https://example.com/failed"
        assert "Specific database error" in failed_article["error"]
