"""
Tests for persistent views that survive bot restarts.

Task 6.3: 撰寫持久化視圖的測試
- 測試 bot 重啟後按鈕仍可運作
- 測試 custom_id 解析
- 測試資料重新載入
- 測試訊息上下文遺失處理

**Validates: Requirements 14.1, 14.2, 14.3, 14.4, 14.5**
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4, UUID

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
    """Create a mock Discord interaction."""
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


@pytest.mark.asyncio
async def test_persistent_read_later_button_saves_article(mock_interaction):
    """Test that PersistentReadLaterButton saves article to reading list."""
    article_id = uuid4()
    mock_interaction.data = {'custom_id': f'read_later_{article_id}'}
    
    # Create a view and add the button to it
    view = discord.ui.View(timeout=None)
    button = PersistentReadLaterButton()
    view.add_item(button)
    
    with patch('app.bot.cogs.persistent_views.SupabaseService') as mock_supabase_class:
        mock_supabase = MagicMock()
        mock_supabase.save_to_reading_list = AsyncMock()
        mock_supabase_class.return_value = mock_supabase
        
        await button.callback(mock_interaction)
        
        # Verify defer was called
        mock_interaction.response.defer.assert_called_once_with(ephemeral=True)
        
        # Verify save_to_reading_list was called with correct parameters
        mock_supabase.save_to_reading_list.assert_called_once_with(
            str(mock_interaction.user.id),
            article_id
        )
        
        # Verify success message was sent
        mock_interaction.followup.send.assert_called_once()
        call_args = mock_interaction.followup.send.call_args
        assert "✅" in call_args[0][0]
        assert call_args[1]['ephemeral'] is True


@pytest.mark.asyncio
async def test_persistent_read_later_button_handles_invalid_custom_id(mock_interaction):
    """Test that PersistentReadLaterButton handles invalid custom_id gracefully."""
    mock_interaction.data = {'custom_id': 'invalid_format'}
    
    view = discord.ui.View(timeout=None)
    button = PersistentReadLaterButton()
    view.add_item(button)
    
    await button.callback(mock_interaction)
    
    # Verify error message was sent
    mock_interaction.followup.send.assert_called_once()
    call_args = mock_interaction.followup.send.call_args
    assert "❌" in call_args[0][0]


@pytest.mark.asyncio
async def test_persistent_mark_read_button_updates_status(mock_interaction):
    """Test that PersistentMarkReadButton updates article status."""
    article_id = uuid4()
    mock_interaction.data = {'custom_id': f'mark_read_{article_id}'}
    
    view = discord.ui.View(timeout=None)
    button = PersistentMarkReadButton()
    view.add_item(button)
    
    with patch('app.bot.cogs.persistent_views.SupabaseService') as mock_supabase_class:
        mock_supabase = MagicMock()
        mock_supabase.update_article_status = AsyncMock()
        mock_supabase_class.return_value = mock_supabase
        
        await button.callback(mock_interaction)
        
        # Verify update_article_status was called with correct parameters
        mock_supabase.update_article_status.assert_called_once_with(
            str(mock_interaction.user.id),
            article_id,
            'Read'
        )
        
        # Verify success message was sent
        mock_interaction.followup.send.assert_called_once()
        call_args = mock_interaction.followup.send.call_args
        assert "✅" in call_args[0][0]


@pytest.mark.asyncio
async def test_persistent_rating_select_updates_rating(mock_interaction):
    """Test that PersistentRatingSelect updates article rating."""
    article_id = uuid4()
    mock_interaction.data = {'custom_id': f'rate_{article_id}'}
    
    view = discord.ui.View(timeout=None)
    select = PersistentRatingSelect()
    view.add_item(select)
    
    # Manually set the internal _values attribute that discord.py uses
    select._values = ['4']
    
    with patch('app.bot.cogs.persistent_views.SupabaseService') as mock_supabase_class:
        mock_supabase = MagicMock()
        mock_supabase.update_article_rating = AsyncMock()
        mock_supabase_class.return_value = mock_supabase
        
        await select.callback(mock_interaction)
        
        # Verify update_article_rating was called with correct parameters
        mock_supabase.update_article_rating.assert_called_once_with(
            str(mock_interaction.user.id),
            article_id,
            4
        )
        
        # Verify success message was sent
        mock_interaction.followup.send.assert_called_once()
        call_args = mock_interaction.followup.send.call_args
        assert "✅" in call_args[0][0]
        assert "4 星" in call_args[0][0]


@pytest.mark.asyncio
async def test_persistent_deep_dive_button_fetches_article_and_generates_analysis(mock_interaction):
    """Test that PersistentDeepDiveButton fetches article and generates deep dive."""
    article_id = uuid4()
    feed_id = uuid4()
    mock_interaction.data = {'custom_id': f'deep_dive_{article_id}'}
    
    view = discord.ui.View(timeout=None)
    button = PersistentDeepDiveButton()
    view.add_item(button)
    
    # Mock article data from database
    mock_article_data = {
        'id': str(article_id),
        'title': 'Test Article',
        'url': 'https://example.com/article',
        'category': 'AI',
        'tinkering_index': 3,
        'ai_summary': 'Test summary',
        'published_at': '2024-01-01T00:00:00+00:00',
        'feed_id': str(feed_id),
        'feed_name': 'Test Feed'
    }
    
    with patch('app.bot.cogs.persistent_views.SupabaseService') as mock_supabase_class, \
         patch('app.bot.cogs.persistent_views.LLMService') as mock_llm_class:
        
        # Mock Supabase response
        mock_supabase = MagicMock()
        mock_response = MagicMock()
        mock_response.data = [mock_article_data]
        mock_supabase.client.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_response
        mock_supabase_class.return_value = mock_supabase
        
        # Mock LLM response
        mock_llm = MagicMock()
        mock_llm.generate_deep_dive = AsyncMock(return_value="Deep dive analysis")
        mock_llm_class.return_value = mock_llm
        
        await button.callback(mock_interaction)
        
        # Verify article was fetched from database
        mock_supabase.client.table.assert_called_once_with('articles')
        
        # Verify LLM was called
        mock_llm.generate_deep_dive.assert_called_once()
        
        # Verify response was sent
        mock_interaction.followup.send.assert_called_once()
        call_args = mock_interaction.followup.send.call_args
        assert "Deep dive analysis" in call_args[0][0]


@pytest.mark.asyncio
async def test_persistent_deep_dive_button_handles_missing_article(mock_interaction):
    """Test that PersistentDeepDiveButton handles missing article gracefully."""
    article_id = uuid4()
    mock_interaction.data = {'custom_id': f'deep_dive_{article_id}'}
    
    view = discord.ui.View(timeout=None)
    button = PersistentDeepDiveButton()
    view.add_item(button)
    
    with patch('app.bot.cogs.persistent_views.SupabaseService') as mock_supabase_class:
        # Mock empty response (article not found)
        mock_supabase = MagicMock()
        mock_response = MagicMock()
        mock_response.data = []
        mock_supabase.client.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_response
        mock_supabase_class.return_value = mock_supabase
        
        await button.callback(mock_interaction)
        
        # Verify error message was sent
        mock_interaction.followup.send.assert_called_once()
        call_args = mock_interaction.followup.send.call_args
        assert "❌" in call_args[0][0]
        assert "找不到" in call_args[0][0]


@pytest.mark.asyncio
async def test_persistent_button_disables_after_click(mock_interaction):
    """Test that persistent buttons disable themselves after successful interaction."""
    article_id = uuid4()
    mock_interaction.data = {'custom_id': f'read_later_{article_id}'}
    
    view = discord.ui.View(timeout=None)
    button = PersistentReadLaterButton()
    view.add_item(button)
    
    with patch('app.bot.cogs.persistent_views.SupabaseService') as mock_supabase_class:
        mock_supabase = MagicMock()
        mock_supabase.save_to_reading_list = AsyncMock()
        mock_supabase_class.return_value = mock_supabase
        
        await button.callback(mock_interaction)
        
        # Verify button was disabled
        assert button.disabled is True
        
        # Verify message was edited
        mock_interaction.message.edit.assert_called_once()


@pytest.mark.asyncio
async def test_persistent_button_handles_message_not_found(mock_interaction):
    """Test that persistent buttons handle message deletion gracefully."""
    article_id = uuid4()
    mock_interaction.data = {'custom_id': f'mark_read_{article_id}'}
    mock_interaction.message.edit = AsyncMock(side_effect=discord.NotFound(MagicMock(), MagicMock()))
    
    view = discord.ui.View(timeout=None)
    button = PersistentMarkReadButton()
    view.add_item(button)
    
    with patch('app.bot.cogs.persistent_views.SupabaseService') as mock_supabase_class:
        mock_supabase = MagicMock()
        mock_supabase.update_article_status = AsyncMock()
        mock_supabase_class.return_value = mock_supabase
        
        # Should not raise exception
        await button.callback(mock_interaction)
        
        # Verify success message was still sent
        mock_interaction.followup.send.assert_called_once()
