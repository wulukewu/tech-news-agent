"""
Task 6.3: 撰寫持久化視圖的測試

Comprehensive tests for persistent views that survive bot restarts.

Test Coverage:
1. Bot 重啟後按鈕仍可運作 (Buttons work after bot restart)
2. Custom_id 解析 (Custom_id parsing)
3. 資料重新載入 (Data reloading from database)
4. 訊息上下文遺失處理 (Message context loss handling)

**Validates: Requirements 14.1, 14.2, 14.3, 14.4, 14.5**
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch, call
from uuid import uuid4, UUID
from datetime import datetime, timezone

import discord

from app.bot.cogs.persistent_views import (
    PersistentReadLaterButton,
    PersistentMarkReadButton,
    PersistentRatingSelect,
    PersistentDeepDiveButton,
    PersistentInteractionView,
    parse_article_id_from_custom_id,
    log_persistent_interaction,
)


@pytest.fixture
def mock_interaction():
    """Create a mock Discord interaction for testing."""
    interaction = MagicMock(spec=discord.Interaction)
    interaction.user = MagicMock()
    interaction.user.id = 123456789
    interaction.response = MagicMock()
    interaction.response.defer = AsyncMock()
    interaction.followup = MagicMock()
    interaction.followup.send = AsyncMock()
    interaction.message = MagicMock()
    interaction.message.edit = AsyncMock()
    interaction.data = {}
    return interaction


# ============================================================================
# Test Suite 1: Bot 重啟後按鈕仍可運作 (Requirement 14.1, 14.2)
# ============================================================================

class TestPostRestartButtonFunctionality:
    """Test that buttons work correctly after bot restart."""
    
    @pytest.mark.asyncio
    async def test_read_later_button_works_after_restart(self, mock_interaction):
        """Test ReadLaterButton functions correctly after bot restart."""
        article_id = uuid4()
        mock_interaction.data = {'custom_id': f'read_later_{article_id}'}
        
        with patch('app.bot.cogs.persistent_views.SupabaseService') as mock_supabase_class:
            mock_supabase = MagicMock()
            mock_supabase.save_to_reading_list = AsyncMock()
            mock_supabase_class.return_value = mock_supabase
            
            # Simulate post-restart interaction
            view = discord.ui.View(timeout=None)
            button = PersistentReadLaterButton()
            view.add_item(button)
            
            await button.callback(mock_interaction)
            
            # Verify button still works
            mock_interaction.response.defer.assert_called_once_with(ephemeral=True)
            mock_supabase.save_to_reading_list.assert_called_once_with(
                str(mock_interaction.user.id), article_id
            )
            mock_interaction.followup.send.assert_called_once()
            assert "✅" in mock_interaction.followup.send.call_args[0][0]
    
    @pytest.mark.asyncio
    async def test_mark_read_button_works_after_restart(self, mock_interaction):
        """Test MarkReadButton functions correctly after bot restart."""
        article_id = uuid4()
        mock_interaction.data = {'custom_id': f'mark_read_{article_id}'}
        
        with patch('app.bot.cogs.persistent_views.SupabaseService') as mock_supabase_class:
            mock_supabase = MagicMock()
            mock_supabase.update_article_status = AsyncMock()
            mock_supabase_class.return_value = mock_supabase
            
            view = discord.ui.View(timeout=None)
            button = PersistentMarkReadButton()
            view.add_item(button)
            
            await button.callback(mock_interaction)
            
            # Verify button still works
            mock_supabase.update_article_status.assert_called_once_with(
                str(mock_interaction.user.id), article_id, 'Read'
            )
            mock_interaction.followup.send.assert_called_once()
            assert "✅" in mock_interaction.followup.send.call_args[0][0]
    
    @pytest.mark.asyncio
    async def test_rating_select_works_after_restart(self, mock_interaction):
        """Test RatingSelect functions correctly after bot restart."""
        article_id = uuid4()
        mock_interaction.data = {'custom_id': f'rate_{article_id}'}
        
        with patch('app.bot.cogs.persistent_views.SupabaseService') as mock_supabase_class:
            mock_supabase = MagicMock()
            mock_supabase.update_article_rating = AsyncMock()
            mock_supabase_class.return_value = mock_supabase
            
            view = discord.ui.View(timeout=None)
            select = PersistentRatingSelect()
            select._values = ['5']  # Simulate user selecting 5 stars
            view.add_item(select)
            
            await select.callback(mock_interaction)
            
            # Verify select still works
            mock_supabase.update_article_rating.assert_called_once_with(
                str(mock_interaction.user.id), article_id, 5
            )
            mock_interaction.followup.send.assert_called_once()
            assert "✅" in mock_interaction.followup.send.call_args[0][0]
            assert "5 星" in mock_interaction.followup.send.call_args[0][0]
    
    @pytest.mark.asyncio
    async def test_persistent_view_has_no_timeout(self):
        """Test that PersistentInteractionView has timeout=None for persistence."""
        view = PersistentInteractionView()
        
        # Verify timeout is None (required for persistence)
        assert view.timeout is None
    
    @pytest.mark.asyncio
    async def test_persistent_view_contains_all_components(self):
        """Test that PersistentInteractionView registers all persistent components."""
        view = PersistentInteractionView()
        
        # Verify all components are registered
        component_types = [type(child) for child in view.children]
        
        assert PersistentReadLaterButton in component_types
        assert PersistentMarkReadButton in component_types
        assert PersistentRatingSelect in component_types
        assert PersistentDeepDiveButton in component_types


# ============================================================================
# Test Suite 2: Custom_id 解析 (Requirement 14.3)
# ============================================================================

class TestCustomIdParsing:
    """Test custom_id parsing logic for all button types."""
    
    def test_parse_read_later_custom_id_valid(self):
        """Test parsing valid read_later custom_id."""
        article_id = uuid4()
        custom_id = f"read_later_{article_id}"
        
        parsed_id = parse_article_id_from_custom_id(custom_id, "read_later_")
        
        assert parsed_id == article_id
        assert isinstance(parsed_id, UUID)
    
    def test_parse_mark_read_custom_id_valid(self):
        """Test parsing valid mark_read custom_id."""
        article_id = uuid4()
        custom_id = f"mark_read_{article_id}"
        
        parsed_id = parse_article_id_from_custom_id(custom_id, "mark_read_")
        
        assert parsed_id == article_id
        assert isinstance(parsed_id, UUID)
    
    def test_parse_rate_custom_id_valid(self):
        """Test parsing valid rate custom_id."""
        article_id = uuid4()
        custom_id = f"rate_{article_id}"
        
        parsed_id = parse_article_id_from_custom_id(custom_id, "rate_")
        
        assert parsed_id == article_id
        assert isinstance(parsed_id, UUID)
    
    def test_parse_deep_dive_custom_id_valid(self):
        """Test parsing valid deep_dive custom_id."""
        article_id = uuid4()
        custom_id = f"deep_dive_{article_id}"
        
        parsed_id = parse_article_id_from_custom_id(custom_id, "deep_dive_")
        
        assert parsed_id == article_id
        assert isinstance(parsed_id, UUID)
    
    def test_parse_custom_id_with_wrong_prefix_raises_error(self):
        """Test that wrong prefix raises ValueError."""
        article_id = uuid4()
        custom_id = f"wrong_prefix_{article_id}"
        
        with pytest.raises(ValueError, match="Invalid custom_id format"):
            parse_article_id_from_custom_id(custom_id, "read_later_")
    
    def test_parse_custom_id_with_invalid_uuid_raises_error(self):
        """Test that invalid UUID raises ValueError."""
        custom_id = "read_later_not-a-valid-uuid"
        
        with pytest.raises(ValueError):
            parse_article_id_from_custom_id(custom_id, "read_later_")
    
    def test_parse_custom_id_with_empty_uuid_raises_error(self):
        """Test that empty UUID raises ValueError."""
        custom_id = "read_later_"
        
        with pytest.raises(ValueError):
            parse_article_id_from_custom_id(custom_id, "read_later_")
    
    @pytest.mark.asyncio
    async def test_button_handles_invalid_custom_id_gracefully(self, mock_interaction):
        """Test that button handles invalid custom_id without crashing."""
        mock_interaction.data = {'custom_id': 'invalid_format_no_uuid'}
        
        view = discord.ui.View(timeout=None)
        button = PersistentReadLaterButton()
        view.add_item(button)
        
        # Should not raise exception
        await button.callback(mock_interaction)
        
        # Verify error message was sent
        mock_interaction.followup.send.assert_called_once()
        assert "❌" in mock_interaction.followup.send.call_args[0][0]


# ============================================================================
# Test Suite 3: 資料重新載入 (Requirement 14.4)
# ============================================================================

class TestDatabaseReloading:
    """Test that data is correctly reloaded from database after restart."""
    
    @pytest.mark.asyncio
    async def test_deep_dive_reloads_article_from_database(self, mock_interaction):
        """
        Test that DeepDiveButton fetches article from database after restart.
        This is critical because article data is not stored in the button.
        """
        article_id = uuid4()
        feed_id = uuid4()
        mock_interaction.data = {'custom_id': f'deep_dive_{article_id}'}
        
        # Mock database response with complete article data
        mock_response = MagicMock()
        mock_response.data = [{
            'id': str(article_id),
            'title': 'Test Article Title',
            'url': 'https://example.com/article',
            'category': 'AI',
            'tinkering_index': 5,
            'ai_summary': 'Test AI summary',
            'published_at': '2024-01-01T00:00:00+00:00',
            'feed_id': str(feed_id),
            'feed_name': 'Test Feed'
        }]
        
        with patch('app.bot.cogs.persistent_views.SupabaseService') as mock_supabase_class, \
             patch('app.bot.cogs.persistent_views.LLMService') as mock_llm_class:
            
            # Setup Supabase mock
            mock_supabase = MagicMock()
            mock_supabase.client.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_response
            mock_supabase_class.return_value = mock_supabase
            
            # Setup LLM mock
            mock_llm = MagicMock()
            mock_llm.generate_deep_dive = AsyncMock(return_value="Deep dive analysis content")
            mock_llm_class.return_value = mock_llm
            
            # Execute button callback
            view = discord.ui.View(timeout=None)
            button = PersistentDeepDiveButton()
            view.add_item(button)
            await button.callback(mock_interaction)
            
            # Verify database was queried for article
            mock_supabase.client.table.assert_called_once_with('articles')
            mock_supabase.client.table.return_value.select.assert_called_once_with('*')
            mock_supabase.client.table.return_value.select.return_value.eq.assert_called_once_with(
                'id', str(article_id)
            )
            
            # Verify LLM was called with reconstructed article
            mock_llm.generate_deep_dive.assert_called_once()
            
            # Verify response was sent
            mock_interaction.followup.send.assert_called_once()
            assert "Deep dive analysis content" in mock_interaction.followup.send.call_args[0][0]
    
    @pytest.mark.asyncio
    async def test_deep_dive_handles_missing_article_gracefully(self, mock_interaction):
        """Test that missing article (deleted from DB) is handled gracefully."""
        article_id = uuid4()
        mock_interaction.data = {'custom_id': f'deep_dive_{article_id}'}
        
        # Mock empty database response (article not found)
        mock_response = MagicMock()
        mock_response.data = []
        
        with patch('app.bot.cogs.persistent_views.SupabaseService') as mock_supabase_class:
            mock_supabase = MagicMock()
            mock_supabase.client.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_response
            mock_supabase_class.return_value = mock_supabase
            
            view = discord.ui.View(timeout=None)
            button = PersistentDeepDiveButton()
            view.add_item(button)
            await button.callback(mock_interaction)
            
            # Verify error message was sent
            mock_interaction.followup.send.assert_called_once_with(
                "❌ 找不到該文章", ephemeral=True
            )
    
    @pytest.mark.asyncio
    async def test_read_later_uses_only_article_id_no_full_data(self, mock_interaction):
        """
        Test that ReadLaterButton only needs article_id, not full article data.
        This verifies efficient database operations.
        """
        article_id = uuid4()
        mock_interaction.data = {'custom_id': f'read_later_{article_id}'}
        
        with patch('app.bot.cogs.persistent_views.SupabaseService') as mock_supabase_class:
            mock_supabase = MagicMock()
            mock_supabase.save_to_reading_list = AsyncMock()
            mock_supabase_class.return_value = mock_supabase
            
            view = discord.ui.View(timeout=None)
            button = PersistentReadLaterButton()
            view.add_item(button)
            await button.callback(mock_interaction)
            
            # Verify only article_id was used (no article fetch)
            mock_supabase.save_to_reading_list.assert_called_once_with(
                str(mock_interaction.user.id), article_id
            )
            # Verify no table queries were made
            assert not mock_supabase.client.table.called


# ============================================================================
# Test Suite 4: 訊息上下文遺失處理 (Requirement 14.5)
# ============================================================================

class TestMessageContextLoss:
    """Test handling of message context loss after bot restart."""
    
    @pytest.mark.asyncio
    async def test_handles_discord_not_found_error(self, mock_interaction):
        """Test that NotFound error (deleted message) is handled gracefully."""
        article_id = uuid4()
        mock_interaction.data = {'custom_id': f'read_later_{article_id}'}
        
        # Simulate message not found (deleted)
        mock_interaction.message.edit = AsyncMock(
            side_effect=discord.NotFound(MagicMock(), MagicMock())
        )
        
        with patch('app.bot.cogs.persistent_views.SupabaseService') as mock_supabase_class:
            mock_supabase = MagicMock()
            mock_supabase.save_to_reading_list = AsyncMock()
            mock_supabase_class.return_value = mock_supabase
            
            view = discord.ui.View(timeout=None)
            button = PersistentReadLaterButton()
            view.add_item(button)
            
            # Should not raise exception
            await button.callback(mock_interaction)
            
            # Verify operation still succeeded
            mock_supabase.save_to_reading_list.assert_called_once()
            
            # Verify user still received confirmation
            mock_interaction.followup.send.assert_called_once()
            assert "✅" in mock_interaction.followup.send.call_args[0][0]
    
    @pytest.mark.asyncio
    async def test_handles_discord_http_exception(self, mock_interaction):
        """Test that HTTPException (rate limit, permissions) is handled gracefully."""
        article_id = uuid4()
        mock_interaction.data = {'custom_id': f'mark_read_{article_id}'}
        
        # Simulate HTTP exception (rate limit, permissions, etc.)
        mock_interaction.message.edit = AsyncMock(
            side_effect=discord.HTTPException(MagicMock(), "Rate limited")
        )
        
        with patch('app.bot.cogs.persistent_views.SupabaseService') as mock_supabase_class:
            mock_supabase = MagicMock()
            mock_supabase.update_article_status = AsyncMock()
            mock_supabase_class.return_value = mock_supabase
            
            view = discord.ui.View(timeout=None)
            button = PersistentMarkReadButton()
            view.add_item(button)
            
            # Should not raise exception
            await button.callback(mock_interaction)
            
            # Verify operation still succeeded
            mock_supabase.update_article_status.assert_called_once()
            
            # Verify user still received confirmation
            mock_interaction.followup.send.assert_called_once()
            assert "✅" in mock_interaction.followup.send.call_args[0][0]
    
    @pytest.mark.asyncio
    async def test_button_disables_even_when_message_edit_fails(self, mock_interaction):
        """Test that button is marked disabled even if message edit fails."""
        article_id = uuid4()
        mock_interaction.data = {'custom_id': f'read_later_{article_id}'}
        mock_interaction.message.edit = AsyncMock(
            side_effect=discord.NotFound(MagicMock(), MagicMock())
        )
        
        with patch('app.bot.cogs.persistent_views.SupabaseService') as mock_supabase_class:
            mock_supabase = MagicMock()
            mock_supabase.save_to_reading_list = AsyncMock()
            mock_supabase_class.return_value = mock_supabase
            
            view = discord.ui.View(timeout=None)
            button = PersistentReadLaterButton()
            view.add_item(button)
            
            await button.callback(mock_interaction)
            
            # Verify button was marked disabled (even though edit failed)
            assert button.disabled is True
    
    @pytest.mark.asyncio
    async def test_operation_succeeds_despite_message_context_loss(self, mock_interaction):
        """
        Test that database operation succeeds even when message context is lost.
        This is the key requirement for post-restart functionality.
        """
        article_id = uuid4()
        mock_interaction.data = {'custom_id': f'mark_read_{article_id}'}
        mock_interaction.message.edit = AsyncMock(
            side_effect=discord.NotFound(MagicMock(), MagicMock())
        )
        
        with patch('app.bot.cogs.persistent_views.SupabaseService') as mock_supabase_class:
            mock_supabase = MagicMock()
            mock_supabase.update_article_status = AsyncMock()
            mock_supabase_class.return_value = mock_supabase
            
            view = discord.ui.View(timeout=None)
            button = PersistentMarkReadButton()
            view.add_item(button)
            
            await button.callback(mock_interaction)
            
            # Verify database operation was called and succeeded
            mock_supabase.update_article_status.assert_called_once_with(
                str(mock_interaction.user.id), article_id, 'Read'
            )


# ============================================================================
# Test Suite 5: 日誌記錄 (Logging for post-restart interactions)
# ============================================================================

class TestPersistentInteractionLogging:
    """Test logging of persistent interactions."""
    
    def test_log_persistent_interaction_success(self):
        """Test logging successful persistent interaction."""
        article_id = uuid4()
        custom_id = f"read_later_{article_id}"
        
        with patch('app.bot.cogs.persistent_views.logger') as mock_logger:
            log_persistent_interaction(
                user_id='123456789',
                action='read_later',
                article_id=article_id,
                custom_id=custom_id,
                success=True
            )
            
            # Verify logger.info was called
            assert mock_logger.info.called
            
            # Verify log contains key information
            log_call = mock_logger.info.call_args
            log_message = log_call[0][0]
            log_data = log_call[1]['extra']
            
            assert 'read_later' in log_message
            assert str(article_id) in log_message
            assert '123456789' in log_message
            
            assert log_data['user_id'] == '123456789'
            assert log_data['action'] == 'read_later'
            assert log_data['article_id'] == str(article_id)
            assert log_data['custom_id'] == custom_id
            assert log_data['success'] is True
            assert log_data['interaction_type'] == 'persistent_view'
            assert 'timestamp' in log_data
    
    def test_log_persistent_interaction_failure(self):
        """Test logging failed persistent interaction."""
        article_id = uuid4()
        custom_id = f"mark_read_{article_id}"
        error_message = "Database connection failed"
        
        with patch('app.bot.cogs.persistent_views.logger') as mock_logger:
            log_persistent_interaction(
                user_id='987654321',
                action='mark_read',
                article_id=article_id,
                custom_id=custom_id,
                success=False,
                error=error_message
            )
            
            # Verify logger.error was called
            assert mock_logger.error.called
            
            # Verify log contains error information
            log_call = mock_logger.error.call_args
            log_message = log_call[0][0]
            log_data = log_call[1]['extra']
            
            assert 'failed' in log_message.lower()
            assert error_message in log_message
            
            assert log_data['success'] is False
            assert log_data['error'] == error_message
    
    @pytest.mark.asyncio
    async def test_button_logs_successful_interaction(self, mock_interaction):
        """Test that button logs successful interaction."""
        article_id = uuid4()
        mock_interaction.data = {'custom_id': f'read_later_{article_id}'}
        
        with patch('app.bot.cogs.persistent_views.SupabaseService') as mock_supabase_class, \
             patch('app.bot.cogs.persistent_views.logger') as mock_logger:
            
            mock_supabase = MagicMock()
            mock_supabase.save_to_reading_list = AsyncMock()
            mock_supabase_class.return_value = mock_supabase
            
            view = discord.ui.View(timeout=None)
            button = PersistentReadLaterButton()
            view.add_item(button)
            await button.callback(mock_interaction)
            
            # Verify logging was called
            assert mock_logger.info.called
            
            # Verify log contains interaction details
            log_calls = [call for call in mock_logger.info.call_args_list]
            assert len(log_calls) > 0
    
    @pytest.mark.asyncio
    async def test_button_logs_failed_interaction(self, mock_interaction):
        """Test that button logs failed interaction."""
        article_id = uuid4()
        mock_interaction.data = {'custom_id': f'mark_read_{article_id}'}
        
        with patch('app.bot.cogs.persistent_views.SupabaseService') as mock_supabase_class, \
             patch('app.bot.cogs.persistent_views.logger') as mock_logger:
            
            # Simulate database error
            mock_supabase = MagicMock()
            mock_supabase.update_article_status = AsyncMock(
                side_effect=Exception("Database connection failed")
            )
            mock_supabase_class.return_value = mock_supabase
            
            view = discord.ui.View(timeout=None)
            button = PersistentMarkReadButton()
            view.add_item(button)
            await button.callback(mock_interaction)
            
            # Verify error logging was called
            assert mock_logger.error.called


# ============================================================================
# Test Suite 6: 端到端測試 (End-to-End Post-Restart Scenarios)
# ============================================================================

class TestEndToEndPostRestartScenarios:
    """End-to-end tests simulating complete post-restart workflows."""
    
    @pytest.mark.asyncio
    async def test_complete_read_later_workflow_after_restart(self, mock_interaction):
        """
        Test complete ReadLater workflow after bot restart:
        1. Parse custom_id
        2. Save to database
        3. Handle message context loss
        4. Log interaction
        5. Confirm to user
        """
        article_id = uuid4()
        custom_id = f'read_later_{article_id}'
        mock_interaction.data = {'custom_id': custom_id}
        mock_interaction.message.edit = AsyncMock(
            side_effect=discord.NotFound(MagicMock(), MagicMock())
        )
        
        with patch('app.bot.cogs.persistent_views.SupabaseService') as mock_supabase_class, \
             patch('app.bot.cogs.persistent_views.logger') as mock_logger:
            
            mock_supabase = MagicMock()
            mock_supabase.save_to_reading_list = AsyncMock()
            mock_supabase_class.return_value = mock_supabase
            
            view = discord.ui.View(timeout=None)
            button = PersistentReadLaterButton()
            view.add_item(button)
            await button.callback(mock_interaction)
            
            # 1. Custom_id was parsed (no exception)
            # 2. Database operation succeeded
            mock_supabase.save_to_reading_list.assert_called_once_with(
                str(mock_interaction.user.id), article_id
            )
            
            # 3. Message context loss was handled
            # 4. Interaction was logged
            assert mock_logger.info.called
            
            # 5. User received confirmation
            mock_interaction.followup.send.assert_called_once()
            assert "✅" in mock_interaction.followup.send.call_args[0][0]
    
    @pytest.mark.asyncio
    async def test_complete_deep_dive_workflow_after_restart(self, mock_interaction):
        """
        Test complete DeepDive workflow after bot restart:
        1. Parse custom_id
        2. Reload article from database
        3. Generate deep dive
        4. Log interaction
        5. Send result to user
        """
        article_id = uuid4()
        feed_id = uuid4()
        custom_id = f'deep_dive_{article_id}'
        mock_interaction.data = {'custom_id': custom_id}
        
        mock_response = MagicMock()
        mock_response.data = [{
            'id': str(article_id),
            'title': 'Test Article',
            'url': 'https://test.com',
            'category': 'AI',
            'tinkering_index': 5,
            'ai_summary': 'Summary',
            'published_at': '2024-01-01T00:00:00+00:00',
            'feed_id': str(feed_id),
            'feed_name': 'Test Feed'
        }]
        
        with patch('app.bot.cogs.persistent_views.SupabaseService') as mock_supabase_class, \
             patch('app.bot.cogs.persistent_views.LLMService') as mock_llm_class, \
             patch('app.bot.cogs.persistent_views.logger') as mock_logger:
            
            mock_supabase = MagicMock()
            mock_supabase.client.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_response
            mock_supabase_class.return_value = mock_supabase
            
            mock_llm = MagicMock()
            mock_llm.generate_deep_dive = AsyncMock(return_value="Deep dive content")
            mock_llm_class.return_value = mock_llm
            
            view = discord.ui.View(timeout=None)
            button = PersistentDeepDiveButton()
            view.add_item(button)
            await button.callback(mock_interaction)
            
            # 1. Custom_id was parsed
            # 2. Article was reloaded from database
            mock_supabase.client.table.assert_called_once_with('articles')
            
            # 3. Deep dive was generated
            mock_llm.generate_deep_dive.assert_called_once()
            
            # 4. Interaction was logged
            assert mock_logger.info.called
            
            # 5. Result was sent to user
            mock_interaction.followup.send.assert_called_once()
            assert "Deep dive content" in mock_interaction.followup.send.call_args[0][0]
    
    @pytest.mark.asyncio
    async def test_multiple_buttons_work_independently_after_restart(self, mock_interaction):
        """Test that multiple button types work independently after restart."""
        article_id_1 = uuid4()
        article_id_2 = uuid4()
        
        with patch('app.bot.cogs.persistent_views.SupabaseService') as mock_supabase_class:
            mock_supabase = MagicMock()
            mock_supabase.save_to_reading_list = AsyncMock()
            mock_supabase.update_article_status = AsyncMock()
            mock_supabase_class.return_value = mock_supabase
            
            # Test ReadLater button
            mock_interaction.data = {'custom_id': f'read_later_{article_id_1}'}
            view1 = discord.ui.View(timeout=None)
            button1 = PersistentReadLaterButton()
            view1.add_item(button1)
            await button1.callback(mock_interaction)
            
            # Test MarkRead button
            mock_interaction.data = {'custom_id': f'mark_read_{article_id_2}'}
            view2 = discord.ui.View(timeout=None)
            button2 = PersistentMarkReadButton()
            view2.add_item(button2)
            await button2.callback(mock_interaction)
            
            # Verify both operations succeeded independently
            mock_supabase.save_to_reading_list.assert_called_once_with(
                str(mock_interaction.user.id), article_id_1
            )
            mock_supabase.update_article_status.assert_called_once_with(
                str(mock_interaction.user.id), article_id_2, 'Read'
            )
    
    @pytest.mark.asyncio
    async def test_rating_select_complete_workflow_after_restart(self, mock_interaction):
        """Test complete rating workflow after bot restart."""
        article_id = uuid4()
        custom_id = f'rate_{article_id}'
        mock_interaction.data = {'custom_id': custom_id}
        
        with patch('app.bot.cogs.persistent_views.SupabaseService') as mock_supabase_class, \
             patch('app.bot.cogs.persistent_views.logger') as mock_logger:
            
            mock_supabase = MagicMock()
            mock_supabase.update_article_rating = AsyncMock()
            mock_supabase_class.return_value = mock_supabase
            
            view = discord.ui.View(timeout=None)
            select = PersistentRatingSelect()
            select._values = ['3']  # User selects 3 stars
            view.add_item(select)
            await select.callback(mock_interaction)
            
            # Verify rating was updated
            mock_supabase.update_article_rating.assert_called_once_with(
                str(mock_interaction.user.id), article_id, 3
            )
            
            # Verify logging
            assert mock_logger.info.called
            
            # Verify user confirmation
            mock_interaction.followup.send.assert_called_once()
            call_args = mock_interaction.followup.send.call_args[0][0]
            assert "✅" in call_args
            assert "3 星" in call_args


# ============================================================================
# Test Suite 7: 錯誤處理 (Error Handling in Post-Restart Scenarios)
# ============================================================================

class TestPostRestartErrorHandling:
    """Test error handling in post-restart scenarios."""
    
    @pytest.mark.asyncio
    async def test_handles_database_connection_error(self, mock_interaction):
        """Test handling of database connection errors."""
        article_id = uuid4()
        mock_interaction.data = {'custom_id': f'read_later_{article_id}'}
        
        with patch('app.bot.cogs.persistent_views.SupabaseService') as mock_supabase_class:
            mock_supabase = MagicMock()
            mock_supabase.save_to_reading_list = AsyncMock(
                side_effect=Exception("Connection timeout")
            )
            mock_supabase_class.return_value = mock_supabase
            
            view = discord.ui.View(timeout=None)
            button = PersistentReadLaterButton()
            view.add_item(button)
            
            # Should not raise exception
            await button.callback(mock_interaction)
            
            # Verify error message was sent
            mock_interaction.followup.send.assert_called_once()
            assert "❌" in mock_interaction.followup.send.call_args[0][0]
    
    @pytest.mark.asyncio
    async def test_handles_malformed_custom_id(self, mock_interaction):
        """Test handling of malformed custom_id."""
        mock_interaction.data = {'custom_id': 'malformed_id_without_uuid'}
        
        view = discord.ui.View(timeout=None)
        button = PersistentReadLaterButton()
        view.add_item(button)
        
        # Should not raise exception
        await button.callback(mock_interaction)
        
        # Verify error message was sent
        mock_interaction.followup.send.assert_called_once()
        assert "❌" in mock_interaction.followup.send.call_args[0][0]
    
    @pytest.mark.asyncio
    async def test_handles_missing_custom_id_in_interaction_data(self, mock_interaction):
        """Test handling when custom_id is missing from interaction data."""
        mock_interaction.data = {}  # No custom_id
        
        view = discord.ui.View(timeout=None)
        button = PersistentMarkReadButton()
        view.add_item(button)
        
        # Should not raise exception
        await button.callback(mock_interaction)
        
        # Verify error message was sent
        mock_interaction.followup.send.assert_called_once()
        assert "❌" in mock_interaction.followup.send.call_args[0][0]
