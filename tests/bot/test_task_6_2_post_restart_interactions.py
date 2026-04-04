"""
Tests for Task 6.2: 處理 bot 重啟後的互動

This test suite verifies that the system correctly handles interactions
after bot restarts, including:
1. Custom_id parsing logic
2. Database data reloading
3. Original message context loss handling
4. Post-restart interaction logging

**Validates: Requirements 14.3, 14.4, 14.5**
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
import discord

from app.bot.cogs.persistent_views import (
    PersistentReadLaterButton,
    PersistentMarkReadButton,
    PersistentRatingSelect,
    PersistentDeepDiveButton,
    parse_article_id_from_custom_id,
    log_persistent_interaction
)


@pytest.fixture
def mock_interaction():
    """Create a mock Discord interaction."""
    interaction = MagicMock(spec=discord.Interaction)
    interaction.user.id = 123456789
    interaction.response.defer = AsyncMock()
    interaction.followup.send = AsyncMock()
    interaction.message.edit = AsyncMock()
    return interaction


class TestCustomIdParsing:
    """Test custom_id parsing logic (Requirement 14.3)."""
    
    def test_parse_read_later_custom_id(self):
        """Test parsing read_later custom_id."""
        article_id = uuid4()
        custom_id = f"read_later_{article_id}"
        
        parsed_id = parse_article_id_from_custom_id(custom_id, "read_later_")
        
        assert parsed_id == article_id
    
    def test_parse_mark_read_custom_id(self):
        """Test parsing mark_read custom_id."""
        article_id = uuid4()
        custom_id = f"mark_read_{article_id}"
        
        parsed_id = parse_article_id_from_custom_id(custom_id, "mark_read_")
        
        assert parsed_id == article_id
    
    def test_parse_rate_custom_id(self):
        """Test parsing rate custom_id."""
        article_id = uuid4()
        custom_id = f"rate_{article_id}"
        
        parsed_id = parse_article_id_from_custom_id(custom_id, "rate_")
        
        assert parsed_id == article_id
    
    def test_parse_deep_dive_custom_id(self):
        """Test parsing deep_dive custom_id."""
        article_id = uuid4()
        custom_id = f"deep_dive_{article_id}"
        
        parsed_id = parse_article_id_from_custom_id(custom_id, "deep_dive_")
        
        assert parsed_id == article_id
    
    def test_parse_invalid_prefix(self):
        """Test parsing with invalid prefix raises ValueError."""
        article_id = uuid4()
        custom_id = f"invalid_{article_id}"
        
        with pytest.raises(ValueError, match="Invalid custom_id format"):
            parse_article_id_from_custom_id(custom_id, "read_later_")
    
    def test_parse_invalid_uuid(self):
        """Test parsing with invalid UUID raises ValueError."""
        custom_id = "read_later_not-a-uuid"
        
        with pytest.raises(ValueError):
            parse_article_id_from_custom_id(custom_id, "read_later_")


class TestDatabaseReloading:
    """Test database data reloading after restart (Requirement 14.4)."""
    
    @pytest.mark.asyncio
    async def test_deep_dive_reloads_article_from_database(self, mock_interaction):
        """
        Test that PersistentDeepDiveButton fetches article from database.
        This is critical for post-restart functionality.
        """
        article_id = uuid4()
        feed_id = uuid4()
        mock_interaction.data = {'custom_id': f'deep_dive_{article_id}'}
        
        # Mock database response
        mock_response = MagicMock()
        mock_response.data = [{
            'id': str(article_id),
            'title': 'Test Article',
            'url': 'https://test.com',
            'category': 'AI',
            'tinkering_index': 5,
            'ai_summary': 'Test summary',
            'published_at': '2024-01-01T00:00:00+00:00',
            'feed_id': str(feed_id),
            'feed_name': 'Test Feed'
        }]
        
        with patch('app.bot.cogs.persistent_views.SupabaseService') as mock_supabase, \
             patch('app.bot.cogs.persistent_views.LLMService') as mock_llm:
            
            # Setup mocks
            mock_supabase_instance = MagicMock()
            mock_supabase_instance.client.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_response
            mock_supabase.return_value = mock_supabase_instance
            
            mock_llm_instance = MagicMock()
            mock_llm_instance.generate_deep_dive = AsyncMock(return_value="Deep dive analysis")
            mock_llm.return_value = mock_llm_instance
            
            # Execute button callback
            view = discord.ui.View(timeout=None)
            button = PersistentDeepDiveButton()
            view.add_item(button)
            await button.callback(mock_interaction)
            
            # Verify database was queried
            mock_supabase_instance.client.table.assert_called_once_with('articles')
            
            # Verify article was fetched by ID
            mock_supabase_instance.client.table.return_value.select.return_value.eq.assert_called_once_with('id', str(article_id))
            
            # Verify LLM was called with reconstructed article
            mock_llm_instance.generate_deep_dive.assert_called_once()
            
            # Verify user received response
            mock_interaction.followup.send.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_deep_dive_handles_missing_article(self, mock_interaction):
        """Test that missing article is handled gracefully."""
        article_id = uuid4()
        mock_interaction.data = {'custom_id': f'deep_dive_{article_id}'}
        
        # Mock empty database response
        mock_response = MagicMock()
        mock_response.data = []
        
        with patch('app.bot.cogs.persistent_views.SupabaseService') as mock_supabase:
            mock_supabase_instance = MagicMock()
            mock_supabase_instance.client.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_response
            mock_supabase.return_value = mock_supabase_instance
            
            view = discord.ui.View(timeout=None)
            button = PersistentDeepDiveButton()
            view.add_item(button)
            await button.callback(mock_interaction)
            
            # Verify user received error message
            mock_interaction.followup.send.assert_called_once_with(
                "❌ 找不到該文章", ephemeral=True
            )


class TestMessageContextLoss:
    """Test handling of original message context loss (Requirement 14.5)."""
    
    @pytest.mark.asyncio
    async def test_handles_message_not_found(self, mock_interaction):
        """Test that message deletion is handled gracefully."""
        article_id = uuid4()
        mock_interaction.data = {'custom_id': f'read_later_{article_id}'}
        
        # Simulate message not found error
        mock_interaction.message.edit = AsyncMock(side_effect=discord.NotFound(MagicMock(), MagicMock()))
        
        with patch('app.bot.cogs.persistent_views.SupabaseService') as mock_supabase:
            mock_supabase_instance = MagicMock()
            mock_supabase_instance.save_to_reading_list = AsyncMock()
            mock_supabase.return_value = mock_supabase_instance
            
            view = discord.ui.View(timeout=None)
            button = PersistentReadLaterButton()
            view.add_item(button)
            await button.callback(mock_interaction)
            
            # Verify operation still succeeded
            mock_supabase_instance.save_to_reading_list.assert_called_once()
            
            # Verify user still received confirmation
            mock_interaction.followup.send.assert_called_once_with(
                "✅ 已加入閱讀清單！", ephemeral=True
            )
    
    @pytest.mark.asyncio
    async def test_handles_http_exception(self, mock_interaction):
        """Test that HTTP exceptions are handled gracefully."""
        article_id = uuid4()
        mock_interaction.data = {'custom_id': f'mark_read_{article_id}'}
        
        # Simulate HTTP exception (rate limit, permissions, etc.)
        mock_interaction.message.edit = AsyncMock(
            side_effect=discord.HTTPException(MagicMock(), "Rate limited")
        )
        
        with patch('app.bot.cogs.persistent_views.SupabaseService') as mock_supabase:
            mock_supabase_instance = MagicMock()
            mock_supabase_instance.update_article_status = AsyncMock()
            mock_supabase.return_value = mock_supabase_instance
            
            view = discord.ui.View(timeout=None)
            button = PersistentMarkReadButton()
            view.add_item(button)
            await button.callback(mock_interaction)
            
            # Verify operation still succeeded
            mock_supabase_instance.update_article_status.assert_called_once()
            
            # Verify user still received confirmation
            mock_interaction.followup.send.assert_called_once_with(
                "✅ 已標記為已讀", ephemeral=True
            )


class TestPostRestartLogging:
    """Test logging of post-restart interactions."""
    
    @pytest.mark.asyncio
    async def test_logs_successful_interaction(self, mock_interaction):
        """Test that successful interactions are logged with full context."""
        article_id = uuid4()
        custom_id = f'read_later_{article_id}'
        mock_interaction.data = {'custom_id': custom_id}
        
        with patch('app.bot.cogs.persistent_views.SupabaseService') as mock_supabase, \
             patch('app.bot.cogs.persistent_views.logger') as mock_logger:
            
            mock_supabase_instance = MagicMock()
            mock_supabase_instance.save_to_reading_list = AsyncMock()
            mock_supabase.return_value = mock_supabase_instance
            
            view = discord.ui.View(timeout=None)
            button = PersistentReadLaterButton()
            view.add_item(button)
            await button.callback(mock_interaction)
            
            # Verify logging was called
            assert mock_logger.info.called
            
            # Verify log contains key information
            log_call = mock_logger.info.call_args
            log_message = log_call[0][0]
            
            assert 'read_later' in log_message
            assert str(article_id) in log_message
            assert str(mock_interaction.user.id) in log_message
    
    @pytest.mark.asyncio
    async def test_logs_failed_interaction(self, mock_interaction):
        """Test that failed interactions are logged with error details."""
        article_id = uuid4()
        custom_id = f'mark_read_{article_id}'
        mock_interaction.data = {'custom_id': custom_id}
        
        with patch('app.bot.cogs.persistent_views.SupabaseService') as mock_supabase, \
             patch('app.bot.cogs.persistent_views.logger') as mock_logger:
            
            # Simulate database error
            mock_supabase_instance = MagicMock()
            mock_supabase_instance.update_article_status = AsyncMock(
                side_effect=Exception("Database connection failed")
            )
            mock_supabase.return_value = mock_supabase_instance
            
            view = discord.ui.View(timeout=None)
            button = PersistentMarkReadButton()
            view.add_item(button)
            await button.callback(mock_interaction)
            
            # Verify error logging was called
            assert mock_logger.error.called
            
            # Verify log contains error information
            error_calls = [call for call in mock_logger.error.call_args_list]
            assert len(error_calls) > 0
    
    def test_log_persistent_interaction_structure(self):
        """Test that log_persistent_interaction creates proper log structure."""
        article_id = uuid4()
        custom_id = f'read_later_{article_id}'
        
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
            
            # Verify log data structure
            log_call = mock_logger.info.call_args
            log_data = log_call[1]['extra']
            
            assert log_data['user_id'] == '123456789'
            assert log_data['action'] == 'read_later'
            assert log_data['article_id'] == str(article_id)
            assert log_data['custom_id'] == custom_id
            assert log_data['success'] is True
            assert log_data['interaction_type'] == 'persistent_view'
            assert 'timestamp' in log_data


class TestEndToEndPostRestart:
    """End-to-end tests simulating bot restart scenarios."""
    
    @pytest.mark.asyncio
    async def test_complete_post_restart_workflow(self, mock_interaction):
        """
        Test complete workflow after bot restart:
        1. Parse custom_id
        2. Reload data from database
        3. Perform action
        4. Handle message context loss
        5. Log interaction
        """
        article_id = uuid4()
        custom_id = f'read_later_{article_id}'
        mock_interaction.data = {'custom_id': custom_id}
        mock_interaction.message.edit = AsyncMock(side_effect=discord.NotFound(MagicMock(), MagicMock()))
        
        with patch('app.bot.cogs.persistent_views.SupabaseService') as mock_supabase, \
             patch('app.bot.cogs.persistent_views.logger') as mock_logger:
            
            mock_supabase_instance = MagicMock()
            mock_supabase_instance.save_to_reading_list = AsyncMock()
            mock_supabase.return_value = mock_supabase_instance
            
            view = discord.ui.View(timeout=None)
            button = PersistentReadLaterButton()
            view.add_item(button)
            await button.callback(mock_interaction)
            
            # 1. Custom_id was parsed (no exception raised)
            # 2. Database was called
            mock_supabase_instance.save_to_reading_list.assert_called_once_with(
                str(mock_interaction.user.id), article_id
            )
            
            # 3. Action was performed
            # 4. Message context loss was handled (NotFound exception caught)
            # 5. Interaction was logged
            assert mock_logger.info.called
            
            # 6. User received confirmation
            mock_interaction.followup.send.assert_called_once_with(
                "✅ 已加入閱讀清單！", ephemeral=True
            )
