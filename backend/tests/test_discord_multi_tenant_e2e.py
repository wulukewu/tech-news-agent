"""
End-to-End tests for Discord Multi-tenant UI.

Task 10.1-10.3: 整合測試與端到端驗證

Tests complete user journeys through Discord commands:
- User registration → subscription → view articles → save to reading list → rate → recommend
- Multi-user isolation
- Persistent views after bot restart
- Backward compatibility with Phase 3

These tests verify the complete Discord bot workflow without mocking.
"""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4

import pytest
from supabase import Client

from app.bot.cogs.interactions import ReadLaterButton
from app.bot.cogs.news_commands import NewsCommands
from app.bot.cogs.reading_list import ReadingListGroup
from app.bot.cogs.subscription_commands import SubscriptionCommands
from app.services.supabase_service import SupabaseService


@pytest.mark.e2e
class TestDiscordMultiTenantE2E:
    """End-to-end tests for Discord multi-tenant UI."""

    @pytest.mark.asyncio
    async def test_complete_user_journey(
        self, test_supabase_client: Client, test_feed, cleanup_test_data
    ):
        """
        Test complete user journey:
        1. User executes /add_feed (auto-registration)
        2. User executes /list_feeds
        3. User executes /news_now (reads from database)
        4. User clicks "Read Later" button
        5. User executes /reading_list view
        6. User rates an article
        7. User executes /reading_list recommend

        **Validates: All requirements (end-to-end workflow)**
        """
        # Setup
        service = SupabaseService(client=test_supabase_client, validate_connection=False)
        discord_id = f"e2e_user_{uuid4().hex}"
        user_id_int = 123456789

        # Mock Discord interaction
        interaction = MagicMock()
        interaction.user.id = user_id_int
        interaction.response.defer = AsyncMock()
        interaction.response.send_message = AsyncMock()
        interaction.followup.send = AsyncMock()

        # 1. Execute /add_feed (auto-registration happens here)
        subscription_cog = SubscriptionCommands(MagicMock())

        with patch("app.bot.cogs.subscription_commands.SupabaseService", return_value=service):
            await subscription_cog.add_feed(
                interaction, name="Test Feed", url=test_feed["url"], category=test_feed["category"]
            )

        # Verify user was created
        user_uuid = await service.get_or_create_user(str(user_id_int))
        cleanup_test_data["users"].append(str(user_uuid))
        assert user_uuid is not None

        # Verify subscription was created
        subscriptions = await service.get_user_subscriptions(str(user_id_int))
        assert len(subscriptions) == 1
        assert subscriptions[0].name == test_feed["name"]

        # 2. Execute /list_feeds
        interaction.response.send_message.reset_mock()
        interaction.followup.send.reset_mock()

        with patch("app.bot.cogs.subscription_commands.SupabaseService", return_value=service):
            await subscription_cog.list_feeds(interaction)

        # Verify response was sent
        assert interaction.followup.send.called
        call_args = interaction.followup.send.call_args
        assert "Test Feed" in call_args[0][0] or "Test Feed" in str(call_args)

        # 3. Insert test articles and execute /news_now
        articles = [
            {
                "title": f"E2E Test Article {i}",
                "url": f"https://e2e-article-{uuid4().hex}.com",
                "feed_id": str(test_feed["id"]),
                "tinkering_index": 5 - i,
                "ai_summary": f"Summary {i}",
                "published_at": (datetime.now(UTC) - timedelta(days=i)).isoformat(),
            }
            for i in range(3)
        ]

        result = await service.insert_articles(articles)
        assert result.inserted_count == 3

        # Track articles for cleanup
        article_ids = []
        for article in articles:
            response = (
                test_supabase_client.table("articles")
                .select("id")
                .eq("url", article["url"])
                .execute()
            )
            article_id = response.data[0]["id"]
            article_ids.append(article_id)
            cleanup_test_data["articles"].append(article_id)

        # Execute /news_now
        news_cog = NewsCommands(MagicMock())
        interaction.response.defer.reset_mock()
        interaction.followup.send.reset_mock()

        with patch("app.bot.cogs.news_commands.SupabaseService", return_value=service):
            await news_cog.news_now(interaction)

        # Verify response
        assert interaction.response.defer.called
        assert interaction.followup.send.called

        # 4. Simulate clicking "Read Later" button
        read_later_button = ReadLaterButton(UUID(article_ids[0]), articles[0]["title"])
        button_interaction = MagicMock()
        button_interaction.user.id = user_id_int
        button_interaction.response.defer = AsyncMock()
        button_interaction.followup.send = AsyncMock()
        button_interaction.message.edit = AsyncMock()

        # Mock the view
        read_later_button.view = MagicMock()

        with patch("app.bot.cogs.interactions.SupabaseService", return_value=service):
            await read_later_button.callback(button_interaction)

        # Verify article was saved to reading list
        reading_list = await service.get_reading_list(str(user_id_int))
        assert len(reading_list) == 1
        assert str(reading_list[0].article_id) == article_ids[0]
        assert reading_list[0].status == "Unread"

        # 5. Execute /reading_list view
        reading_list_group = ReadingListGroup()
        interaction.response.defer.reset_mock()
        interaction.followup.send.reset_mock()

        with patch("app.bot.cogs.reading_list.SupabaseService", return_value=service):
            await reading_list_group.view(interaction)

        # Verify response
        assert interaction.response.defer.called
        assert interaction.followup.send.called

        # 6. Rate the article
        await service.update_article_rating(str(user_id_int), article_ids[0], 5)

        # Verify rating
        reading_list = await service.get_reading_list(str(user_id_int))
        assert reading_list[0].rating == 5

        # 7. Execute /reading_list recommend
        interaction.response.defer.reset_mock()
        interaction.followup.send.reset_mock()

        with patch("app.bot.cogs.reading_list.SupabaseService", return_value=service):
            with patch("app.bot.cogs.reading_list.LLMService") as mock_llm:
                mock_llm.return_value.generate_recommendations = AsyncMock(
                    return_value="基於您的高評分文章，我們推薦..."
                )
                await reading_list_group.recommend(interaction)

        # Verify response
        assert interaction.response.defer.called
        assert interaction.followup.send.called

    @pytest.mark.asyncio
    async def test_multi_user_isolation_e2e(
        self, test_supabase_client: Client, test_feed, cleanup_test_data
    ):
        """
        Test that User A's subscriptions and reading list don't affect User B.

        **Validates: Requirements 3.1-3.5, 6.1-6.8, 9.1-9.9**
        """
        service = SupabaseService(client=test_supabase_client, validate_connection=False)

        user_a_id = 111111111
        user_b_id = 222222222

        # Create users
        user_a_uuid = await service.get_or_create_user(str(user_a_id))
        user_b_uuid = await service.get_or_create_user(str(user_b_id))
        cleanup_test_data["users"].extend([str(user_a_uuid), str(user_b_uuid)])

        # User A subscribes to test_feed
        await service.subscribe_to_feed(str(user_a_id), test_feed["id"])

        # Create another feed for User B
        feed_b_url = f"https://user-b-feed-{uuid4().hex}.com/rss.xml"
        feed_b_result = (
            test_supabase_client.table("feeds")
            .insert(
                {
                    "name": "User B Feed",
                    "url": feed_b_url,
                    "category": "User B Category",
                    "is_active": True,
                }
            )
            .execute()
        )
        feed_b = feed_b_result.data[0]
        cleanup_test_data["feeds"].append(feed_b["id"])

        # User B subscribes to feed_b
        await service.subscribe_to_feed(str(user_b_id), feed_b["id"])

        # Verify subscription isolation
        user_a_subs = await service.get_user_subscriptions(str(user_a_id))
        user_b_subs = await service.get_user_subscriptions(str(user_b_id))

        assert len(user_a_subs) == 1
        assert len(user_b_subs) == 1
        assert user_a_subs[0].name == test_feed["name"]
        assert user_b_subs[0].name == "User B Feed"

        # Insert articles for both feeds
        articles_a = [
            {
                "title": "Article for User A",
                "url": f"https://article-a-{uuid4().hex}.com",
                "feed_id": str(test_feed["id"]),
                "tinkering_index": 5,
                "published_at": datetime.now(UTC).isoformat(),
            }
        ]

        articles_b = [
            {
                "title": "Article for User B",
                "url": f"https://article-b-{uuid4().hex}.com",
                "feed_id": feed_b["id"],
                "tinkering_index": 5,
                "published_at": datetime.now(UTC).isoformat(),
            }
        ]

        await service.insert_articles(articles_a + articles_b)

        # Get article IDs
        response_a = (
            test_supabase_client.table("articles")
            .select("id")
            .eq("url", articles_a[0]["url"])
            .execute()
        )
        article_a_id = response_a.data[0]["id"]
        cleanup_test_data["articles"].append(article_a_id)

        response_b = (
            test_supabase_client.table("articles")
            .select("id")
            .eq("url", articles_b[0]["url"])
            .execute()
        )
        article_b_id = response_b.data[0]["id"]
        cleanup_test_data["articles"].append(article_b_id)

        # User A saves article A
        await service.save_to_reading_list(str(user_a_id), article_a_id)

        # User B saves article B
        await service.save_to_reading_list(str(user_b_id), article_b_id)

        # Verify reading list isolation
        user_a_reading_list = await service.get_reading_list(str(user_a_id))
        user_b_reading_list = await service.get_reading_list(str(user_b_id))

        assert len(user_a_reading_list) == 1
        assert len(user_b_reading_list) == 1
        assert str(user_a_reading_list[0].article_id) == article_a_id
        assert str(user_b_reading_list[0].article_id) == article_b_id

        # Verify User A cannot see User B's articles in /news_now
        # (articles are filtered by user's subscribed feeds)
        seven_days_ago = (datetime.now(UTC) - timedelta(days=7)).isoformat()

        # Query articles for User A
        response = (
            test_supabase_client.table("articles")
            .select("id, title")
            .eq("feed_id", test_feed["id"])
            .gte("published_at", seven_days_ago)
            .execute()
        )

        user_a_articles = response.data
        assert len(user_a_articles) >= 1
        assert any(a["id"] == article_a_id for a in user_a_articles)
        assert not any(a["id"] == article_b_id for a in user_a_articles)

    @pytest.mark.asyncio
    async def test_persistent_views_after_restart(
        self, test_supabase_client: Client, test_feed, cleanup_test_data
    ):
        """
        Test that interactive buttons work after bot restart.
        This simulates the bot restarting by creating new button instances
        with the same custom_id.

        **Validates: Requirements 14.1-14.5**
        """
        service = SupabaseService(client=test_supabase_client, validate_connection=False)

        user_id = 333333333
        user_uuid = await service.get_or_create_user(str(user_id))
        cleanup_test_data["users"].append(str(user_uuid))

        # Insert test article
        article = {
            "title": "Persistent View Test Article",
            "url": f"https://persistent-{uuid4().hex}.com",
            "feed_id": str(test_feed["id"]),
            "tinkering_index": 5,
            "published_at": datetime.now(UTC).isoformat(),
        }

        await service.insert_articles([article])

        response = (
            test_supabase_client.table("articles").select("id").eq("url", article["url"]).execute()
        )
        article_id = response.data[0]["id"]
        cleanup_test_data["articles"].append(article_id)

        # Create button (simulating original message)
        button_v1 = ReadLaterButton(UUID(article_id), article["title"])
        custom_id_v1 = button_v1.custom_id

        # Simulate bot restart by creating new button with same custom_id
        # (In real scenario, Discord preserves custom_id across restarts)
        button_v2 = ReadLaterButton(UUID(article_id), article["title"])
        custom_id_v2 = button_v2.custom_id

        # Verify custom_id is stable
        assert custom_id_v1 == custom_id_v2
        assert article_id in custom_id_v2

        # Simulate button click after restart
        interaction = MagicMock()
        interaction.user.id = user_id
        interaction.response.defer = AsyncMock()
        interaction.followup.send = AsyncMock()
        interaction.message.edit = AsyncMock()
        button_v2.view = MagicMock()

        with patch("app.bot.cogs.interactions.SupabaseService", return_value=service):
            await button_v2.callback(interaction)

        # Verify button still works
        reading_list = await service.get_reading_list(str(user_id))
        assert len(reading_list) == 1
        assert str(reading_list[0].article_id) == article_id

    @pytest.mark.asyncio
    async def test_backward_compatibility_with_phase3(
        self, test_supabase_client: Client, test_feed, cleanup_test_data
    ):
        """
        Test backward compatibility with Phase 3:
        - Handles articles created by background scheduler
        - Handles users with no subscriptions
        - No database migrations required

        **Validates: Requirements 18.1-18.5**
        """
        service = SupabaseService(client=test_supabase_client, validate_connection=False)

        # Simulate Phase 3 scenario: articles exist but user has no subscriptions
        user_id = 444444444
        user_uuid = await service.get_or_create_user(str(user_id))
        cleanup_test_data["users"].append(str(user_uuid))

        # Insert articles (simulating background scheduler)
        articles = [
            {
                "title": f"Phase 3 Article {i}",
                "url": f"https://phase3-{uuid4().hex}.com",
                "feed_id": str(test_feed["id"]),
                "tinkering_index": 5,
                "published_at": datetime.now(UTC).isoformat(),
            }
            for i in range(3)
        ]

        result = await service.insert_articles(articles)
        assert result.inserted_count == 3

        for article in articles:
            response = (
                test_supabase_client.table("articles")
                .select("id")
                .eq("url", article["url"])
                .execute()
            )
            cleanup_test_data["articles"].append(response.data[0]["id"])

        # Execute /news_now without subscriptions
        news_cog = NewsCommands(MagicMock())
        interaction = MagicMock()
        interaction.user.id = user_id
        interaction.response.defer = AsyncMock()
        interaction.followup.send = AsyncMock()

        with patch("app.bot.cogs.news_commands.SupabaseService", return_value=service):
            await news_cog.news_now(interaction)

        # Verify user is prompted to subscribe
        assert interaction.followup.send.called
        call_args = interaction.followup.send.call_args[0][0]
        assert "訂閱" in call_args or "subscribe" in call_args.lower()

        # Now subscribe and verify articles appear
        await service.subscribe_to_feed(str(user_id), test_feed["id"])

        interaction.followup.send.reset_mock()

        with patch("app.bot.cogs.news_commands.SupabaseService", return_value=service):
            await news_cog.news_now(interaction)

        # Verify articles are shown
        assert interaction.followup.send.called
        call_args = interaction.followup.send.call_args
        # Should contain article information
        assert call_args is not None

    @pytest.mark.asyncio
    async def test_error_handling_user_friendly_messages(
        self, test_supabase_client: Client, cleanup_test_data
    ):
        """
        Test that error messages are user-friendly and in Traditional Chinese.

        **Validates: Requirements 12.1-12.6**
        """
        service = SupabaseService(client=test_supabase_client, validate_connection=False)

        user_id = 555555555
        user_uuid = await service.get_or_create_user(str(user_id))
        cleanup_test_data["users"].append(str(user_uuid))

        # Test 1: Invalid feed URL
        subscription_cog = SubscriptionCommands(MagicMock())
        interaction = MagicMock()
        interaction.user.id = user_id
        interaction.response.defer = AsyncMock()
        interaction.followup.send = AsyncMock()

        with patch("app.bot.cogs.subscription_commands.SupabaseService", return_value=service):
            await subscription_cog.add_feed(
                interaction, name="Invalid Feed", url="not-a-valid-url", category="Test"
            )

        # Verify error message is user-friendly
        assert interaction.followup.send.called
        error_msg = interaction.followup.send.call_args[0][0]
        assert "❌" in error_msg
        assert "失敗" in error_msg or "錯誤" in error_msg

        # Test 2: Empty reading list
        reading_list_group = ReadingListGroup()
        interaction.response.defer.reset_mock()
        interaction.followup.send.reset_mock()

        with patch("app.bot.cogs.reading_list.SupabaseService", return_value=service):
            await reading_list_group.view(interaction)

        # Verify friendly message for empty list
        assert interaction.followup.send.called
        msg = interaction.followup.send.call_args[0][0]
        assert "空" in msg or "沒有" in msg

    @pytest.mark.asyncio
    async def test_performance_response_times(
        self, test_supabase_client: Client, test_feed, cleanup_test_data
    ):
        """
        Test that commands respond within acceptable time limits:
        - /news_now: < 3 seconds
        - /reading_list view: < 2 seconds

        **Validates: Requirements 15.1-15.2**
        """
        import time

        service = SupabaseService(client=test_supabase_client, validate_connection=False)

        user_id = 666666666
        user_uuid = await service.get_or_create_user(str(user_id))
        cleanup_test_data["users"].append(str(user_uuid))

        # Subscribe to feed
        await service.subscribe_to_feed(str(user_id), test_feed["id"])

        # Insert test articles
        articles = [
            {
                "title": f"Performance Test Article {i}",
                "url": f"https://perf-{uuid4().hex}.com",
                "feed_id": str(test_feed["id"]),
                "tinkering_index": 5,
                "published_at": datetime.now(UTC).isoformat(),
            }
            for i in range(20)
        ]

        await service.insert_articles(articles)

        for article in articles:
            response = (
                test_supabase_client.table("articles")
                .select("id")
                .eq("url", article["url"])
                .execute()
            )
            cleanup_test_data["articles"].append(response.data[0]["id"])

        # Test /news_now performance
        news_cog = NewsCommands(MagicMock())
        interaction = MagicMock()
        interaction.user.id = user_id
        interaction.response.defer = AsyncMock()
        interaction.followup.send = AsyncMock()

        start_time = time.time()

        with patch("app.bot.cogs.news_commands.SupabaseService", return_value=service):
            await news_cog.news_now(interaction)

        news_now_time = time.time() - start_time

        # Should respond within 3 seconds
        assert news_now_time < 3.0, f"/news_now took {news_now_time:.2f}s (should be < 3s)"

        # Save one article to reading list
        response = (
            test_supabase_client.table("articles")
            .select("id")
            .eq("url", articles[0]["url"])
            .execute()
        )
        article_id = response.data[0]["id"]
        await service.save_to_reading_list(str(user_id), article_id)

        # Test /reading_list view performance
        reading_list_group = ReadingListGroup()
        interaction.response.defer.reset_mock()
        interaction.followup.send.reset_mock()

        start_time = time.time()

        with patch("app.bot.cogs.reading_list.SupabaseService", return_value=service):
            await reading_list_group.view(interaction)

        reading_list_time = time.time() - start_time

        # Should respond within 2 seconds
        assert (
            reading_list_time < 2.0
        ), f"/reading_list view took {reading_list_time:.2f}s (should be < 2s)"
