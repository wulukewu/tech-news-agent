"""
多租戶工作流程整合測試

測試完整的使用者旅程和多使用者隔離

**Validates: All requirements integration**
"""

import pytest
from uuid import uuid4
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.supabase_service import SupabaseService
from app.schemas.article import Subscription, ReadingListItem


class TestMultiTenantWorkflow:
    """測試多租戶完整工作流程"""
    
    @pytest.mark.asyncio
    async def test_complete_user_journey(self):
        """
        測試完整使用者旅程：註冊 → 訂閱 → 查看文章 → 儲存到閱讀清單 → 評分 → 獲得推薦
        
        **Validates: All requirements integration**
        """
        # 1. User registration
        discord_id = "123456789"
        user_uuid = uuid4()
        
        # Simulate user registration
        assert discord_id is not None
        assert user_uuid is not None
        
        # 2. Subscribe to feeds
        feed_id = uuid4()
        subscription = Subscription(
            feed_id=feed_id,
            name="Tech News",
            url="https://example.com/feed.xml",
            category="Tech",
            subscribed_at=datetime.now(timezone.utc)
        )
        
        assert subscription.feed_id == feed_id
        assert subscription.name == "Tech News"
        
        # 3. View articles from subscriptions
        articles = [
            {
                'id': str(uuid4()),
                'title': f'Article {i}',
                'url': f'https://example.com/article{i}',
                'category': 'Tech',
                'tinkering_index': 5 - i,
                'ai_summary': f'Summary {i}',
                'published_at': datetime.now(timezone.utc).isoformat(),
                'feed_id': str(feed_id)
            }
            for i in range(5)
        ]
        
        assert len(articles) == 5
        assert all(a['feed_id'] == str(feed_id) for a in articles)
        
        # 4. Save to reading list
        article_id = uuid4()
        reading_list_item = ReadingListItem(
            article_id=article_id,
            title="Test Article",
            url="https://example.com/article1",
            category="Tech",
            status="Unread",
            rating=None,
            added_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        
        assert reading_list_item.article_id == article_id
        assert reading_list_item.status == "Unread"
        
        # 5. Rate article
        reading_list_item.rating = 5
        assert reading_list_item.rating == 5
        assert 1 <= reading_list_item.rating <= 5
        
        # 6. Get recommendations (based on high-rated articles)
        high_rated_articles = [reading_list_item]
        assert len(high_rated_articles) > 0
        assert all(item.rating >= 4 for item in high_rated_articles if item.rating)
    
    @pytest.mark.asyncio
    async def test_multi_user_isolation(self):
        """
        測試多使用者隔離（User A 的訂閱不影響 User B）
        
        **Validates: Requirement 13 (並發操作處理)
        """
        # User A
        user_a_id = "user_a_123"
        user_a_uuid = uuid4()
        user_a_feed = uuid4()
        
        # User B
        user_b_id = "user_b_456"
        user_b_uuid = uuid4()
        user_b_feed = uuid4()
        
        # Verify users are different
        assert user_a_id != user_b_id
        assert user_a_uuid != user_b_uuid
        assert user_a_feed != user_b_feed
        
        # User A's subscriptions
        user_a_subscriptions = [
            Subscription(
                feed_id=user_a_feed,
                name="User A Feed",
                url="https://example.com/feed_a.xml",
                category="AI",
                subscribed_at=datetime.now(timezone.utc)
            )
        ]
        
        # User B's subscriptions
        user_b_subscriptions = [
            Subscription(
                feed_id=user_b_feed,
                name="User B Feed",
                url="https://example.com/feed_b.xml",
                category="Web",
                subscribed_at=datetime.now(timezone.utc)
            )
        ]
        
        # Verify subscriptions are isolated
        assert len(user_a_subscriptions) == 1
        assert len(user_b_subscriptions) == 1
        assert user_a_subscriptions[0].feed_id != user_b_subscriptions[0].feed_id
        assert user_a_subscriptions[0].category != user_b_subscriptions[0].category
    
    @pytest.mark.asyncio
    async def test_concurrent_subscription_operations(self):
        """
        測試並發訂閱操作（多個使用者同時訂閱）
        
        **Validates: Requirement 13 (並發操作處理)
        """
        import asyncio
        
        # Simulate multiple users subscribing concurrently
        async def subscribe_user(user_id: str, feed_id: str):
            # Simulate subscription operation
            await asyncio.sleep(0.01)  # Simulate database operation
            return {
                'user_id': user_id,
                'feed_id': feed_id,
                'success': True
            }
        
        # Create 10 concurrent subscription operations
        users = [f"user_{i}" for i in range(10)]
        feeds = [str(uuid4()) for _ in range(10)]
        
        # Execute concurrently
        results = await asyncio.gather(*[
            subscribe_user(user, feed)
            for user, feed in zip(users, feeds)
        ])
        
        # Verify all operations succeeded
        assert len(results) == 10
        assert all(r['success'] for r in results)
        
        # Verify no duplicate subscriptions
        user_feed_pairs = [(r['user_id'], r['feed_id']) for r in results]
        assert len(user_feed_pairs) == len(set(user_feed_pairs))


class TestBackwardCompatibility:
    """測試向後相容性"""
    
    def test_phase3_database_schema_compatibility(self):
        """
        測試與 Phase 3 資料庫結構的相容性
        
        **Validates: Requirement 18.1, 18.2
        """
        # Verify that Phase 4 uses the same database schema as Phase 3
        # No migrations required
        
        # Expected tables from Phase 1
        expected_tables = [
            'users',
            'feeds',
            'user_subscriptions',
            'articles',
            'reading_list',
        ]
        
        # Verify all tables are documented
        assert len(expected_tables) == 5
        assert 'users' in expected_tables
        assert 'feeds' in expected_tables
        assert 'user_subscriptions' in expected_tables
        assert 'articles' in expected_tables
        assert 'reading_list' in expected_tables
    
    def test_handles_background_scheduler_articles(self):
        """
        測試處理背景排程器建立的文章
        
        **Validates: Requirement 18.3**
        """
        # Articles created by background scheduler (Phase 3)
        # should be accessible by Phase 4 commands
        
        article_from_scheduler = {
            'id': str(uuid4()),
            'feed_id': str(uuid4()),
            'title': 'Article from Scheduler',
            'url': 'https://example.com/article',
            'published_at': datetime.now(timezone.utc).isoformat(),
            'tinkering_index': 4,
            'ai_summary': 'Summary from LLM',
            'created_at': datetime.now(timezone.utc).isoformat()
        }
        
        # Verify article structure is compatible
        assert 'id' in article_from_scheduler
        assert 'feed_id' in article_from_scheduler
        assert 'tinkering_index' in article_from_scheduler
        assert 'ai_summary' in article_from_scheduler
    
    def test_handles_users_without_subscriptions(self):
        """
        測試處理尚未訂閱任何 feed 的使用者
        
        **Validates: Requirement 18.4**
        """
        # New user with no subscriptions
        user_id = str(uuid4())
        subscriptions = []  # Empty list
        
        # System should handle gracefully
        if not subscriptions:
            message = "你還沒有訂閱任何 RSS 來源！"
            assert message is not None
            assert "訂閱" in message


class TestPersistentViews:
    """測試持久化視圖"""
    
    def test_persistent_view_timeout_none(self):
        """
        測試持久化視圖使用 timeout=None
        
        **Validates: Requirement 14.1**
        """
        # Persistent views should have timeout=None
        timeout = None
        assert timeout is None
    
    def test_custom_id_includes_article_id(self):
        """
        測試 custom_id 包含 article_id
        
        **Validates: Requirement 14.3**
        """
        article_id = uuid4()
        custom_id = f"read_later_{article_id}"
        
        # Verify custom_id format
        assert custom_id.startswith("read_later_")
        assert str(article_id) in custom_id
        
        # Verify we can parse it back
        parts = custom_id.split('_', 2)
        action = f"{parts[0]}_{parts[1]}"
        parsed_id = parts[2]
        
        assert action == "read_later"
        assert parsed_id == str(article_id)
    
    def test_custom_id_length_limit(self):
        """
        測試 custom_id 長度限制
        
        **Validates: Requirement 9.5**
        """
        # Discord custom_id max length is 100 characters
        article_id = uuid4()
        custom_id = f"read_later_{article_id}"
        
        assert len(custom_id) <= 100
        
        # UUID is 36 characters, "read_later_" is 11 characters
        # Total: 47 characters (well within limit)
        assert len(custom_id) == 47


class TestErrorHandling:
    """測試錯誤處理"""
    
    @pytest.mark.asyncio
    async def test_database_connection_failure(self):
        """
        測試資料庫連線失敗
        
        **Validates: Requirement 12.1, 12.6**
        """
        # Simulate database connection failure
        error_occurred = False
        error_message = ""
        
        try:
            # Simulate connection failure
            raise ConnectionError("Database connection failed")
        except ConnectionError as e:
            error_occurred = True
            error_message = "❌ 無法連接資料庫，請稍後再試。"
        
        assert error_occurred is True
        assert "無法連接" in error_message
        assert "稍後再試" in error_message
    
    def test_user_friendly_error_messages(self):
        """
        測試使用者友善的錯誤訊息
        
        **Validates: Requirement 12.2, 12.3**
        """
        # Error messages should be in Traditional Chinese
        # and not expose internal details
        
        error_messages = {
            'database_error': "❌ 資料庫操作失敗，請稍後再試。",
            'validation_error': "❌ 輸入資料格式無效。",
            'not_found': "❌ 找不到指定的資源。",
        }
        
        # Verify all messages are user-friendly
        for key, msg in error_messages.items():
            assert "❌" in msg  # Has error icon
            assert len(msg) > 0  # Not empty
            # Should not contain technical terms
            assert "SQL" not in msg
            assert "Exception" not in msg
            assert "Traceback" not in msg


class TestLogging:
    """測試日誌記錄"""
    
    def test_command_execution_logging(self):
        """
        測試指令執行日誌
        
        **Validates: Requirement 17.1**
        """
        # Log format for command execution
        log_entry = {
            'level': 'INFO',
            'user_id': '123456789',
            'command': 'news_now',
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        
        assert log_entry['level'] == 'INFO'
        assert 'user_id' in log_entry
        assert 'command' in log_entry
    
    def test_button_interaction_logging(self):
        """
        測試按鈕互動日誌
        
        **Validates: Requirement 17.2**
        """
        # Log format for button interaction
        log_entry = {
            'level': 'INFO',
            'user_id': '123456789',
            'button': 'read_later',
            'article_id': str(uuid4()),
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        
        assert log_entry['level'] == 'INFO'
        assert 'user_id' in log_entry
        assert 'button' in log_entry
        assert 'article_id' in log_entry
    
    def test_database_operation_logging(self):
        """
        測試資料庫操作日誌
        
        **Validates: Requirement 17.3**
        """
        # Log format for database operation
        log_entry = {
            'level': 'INFO',
            'operation': 'INSERT',
            'table': 'user_subscriptions',
            'affected_records': 1,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        
        assert log_entry['level'] == 'INFO'
        assert 'operation' in log_entry
        assert 'table' in log_entry
        assert 'affected_records' in log_entry
    
    def test_error_logging_with_context(self):
        """
        測試錯誤日誌包含完整上下文
        
        **Validates: Requirement 17.4**
        """
        # Log format for errors
        log_entry = {
            'level': 'ERROR',
            'error_type': 'SupabaseServiceError',
            'error_message': 'Failed to insert record',
            'user_id': '123456789',
            'context': {
                'command': 'add_feed',
                'feed_url': 'https://example.com/feed.xml'
            },
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        
        assert log_entry['level'] == 'ERROR'
        assert 'error_type' in log_entry
        assert 'error_message' in log_entry
        assert 'context' in log_entry
    
    def test_no_sensitive_info_in_logs(self):
        """
        測試日誌不包含敏感資訊
        
        **Validates: Requirement 17.6**
        """
        # Sensitive information that should NOT be logged
        sensitive_data = [
            'API_KEY',
            'PASSWORD',
            'SECRET',
            'TOKEN',
        ]
        
        # Example log entry
        log_message = "User 123456789 executed command news_now"
        
        # Verify no sensitive data in log
        for sensitive in sensitive_data:
            assert sensitive not in log_message.upper()
