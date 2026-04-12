"""
Unit tests for interactive buttons (ReadLaterButton, MarkReadButton, RatingSelect)
Task 4.6: 撰寫互動按鈕的單元測試
Validates: Requirements 4.1-4.8, 5.1-5.7, 7.1-7.6, 9.1-9.6
"""

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4

import discord
import pytest

from app.bot.cogs.interactions import MarkReadButton, ReadLaterButton
from app.bot.cogs.reading_list import MarkAsReadButton, RatingSelect
from app.core.exceptions import SupabaseServiceError
from app.schemas.article import ReadingListItem

# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------


def make_interaction():
    """Create a mock Discord interaction."""
    interaction = MagicMock(spec=discord.Interaction)
    interaction.response = MagicMock()
    interaction.response.defer = AsyncMock()
    interaction.followup = MagicMock()
    interaction.followup.send = AsyncMock()
    interaction.message = MagicMock()
    interaction.message.edit = AsyncMock()
    interaction.user = MagicMock()
    interaction.user.id = 123456789
    return interaction


def make_reading_list_item(article_id=None, title="Test Article", rating=None):
    """Create a ReadingListItem for testing."""
    if article_id is None:
        article_id = uuid4()
    from datetime import datetime

    return ReadingListItem(
        article_id=article_id,
        title=title,
        url="https://example.com/article",
        category="AI",
        status="Unread",
        rating=rating,
        added_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )


# ---------------------------------------------------------------------------
# Task 4.6.1 — ReadLaterButton 儲存文章
# ---------------------------------------------------------------------------


class TestReadLaterButtonSaveArticle:
    @pytest.mark.asyncio
    async def test_save_article_success(self):
        """ReadLaterButton successfully saves article to reading list."""
        article_id = uuid4()
        button = ReadLaterButton(article_id, "Test Article")
        interaction = make_interaction()

        with patch("app.bot.cogs.interactions.SupabaseService") as MockSupabase:
            instance = MockSupabase.return_value
            instance.save_to_reading_list = AsyncMock(return_value=None)

            await button.callback(interaction)

            # Verify save_to_reading_list was called with correct parameters
            instance.save_to_reading_list.assert_called_once_with(
                str(interaction.user.id), article_id
            )

            # Verify button was disabled
            assert button.disabled is True

            # Verify confirmation message was sent
            interaction.followup.send.assert_called_once()
            call_args = interaction.followup.send.call_args
            assert "✅ 已加入閱讀清單！" in call_args[0][0]
            assert call_args[1]["ephemeral"] is True


# ---------------------------------------------------------------------------
# Task 4.6.2 — ReadLaterButton 重複儲存
# ---------------------------------------------------------------------------


class TestReadLaterButtonDuplicateSave:
    @pytest.mark.asyncio
    async def test_duplicate_save_handled_gracefully(self):
        """ReadLaterButton handles duplicate save attempts gracefully."""
        article_id = uuid4()
        button = ReadLaterButton(article_id, "Test Article")
        interaction = make_interaction()

        with patch("app.bot.cogs.interactions.SupabaseService") as MockSupabase:
            instance = MockSupabase.return_value
            # Simulate duplicate save (UPSERT behavior - no error)
            instance.save_to_reading_list = AsyncMock(return_value=None)

            await button.callback(interaction)

            # Should still succeed and disable button
            assert button.disabled is True
            interaction.followup.send.assert_called_once()


# ---------------------------------------------------------------------------
# Task 4.6.3 — MarkReadButton 更新狀態
# ---------------------------------------------------------------------------


class TestMarkReadButtonUpdateStatus:
    @pytest.mark.asyncio
    async def test_mark_read_success(self):
        """MarkReadButton successfully updates article status to Read."""
        article_id = uuid4()
        button = MarkReadButton(article_id, "Test Article")
        interaction = make_interaction()

        with patch("app.bot.cogs.interactions.SupabaseService") as MockSupabase:
            instance = MockSupabase.return_value
            instance.update_article_status = AsyncMock(return_value=None)

            await button.callback(interaction)

            # Verify update_article_status was called with correct parameters
            instance.update_article_status.assert_called_once_with(
                str(interaction.user.id), article_id, "Read"
            )

            # Verify button was disabled
            assert button.disabled is True

            # Verify confirmation message was sent
            interaction.followup.send.assert_called_once()
            call_args = interaction.followup.send.call_args
            assert "✅ 已標記為已讀" in call_args[0][0]
            assert call_args[1]["ephemeral"] is True


# ---------------------------------------------------------------------------
# Task 4.6.4 — MarkReadButton 自動加入閱讀清單
# ---------------------------------------------------------------------------


class TestMarkReadButtonAutoAdd:
    @pytest.mark.asyncio
    async def test_mark_read_auto_adds_to_reading_list(self):
        """MarkReadButton adds article to reading list if not present."""
        article_id = uuid4()
        button = MarkReadButton(article_id, "Test Article")
        interaction = make_interaction()

        with patch("app.bot.cogs.interactions.SupabaseService") as MockSupabase:
            instance = MockSupabase.return_value
            # update_article_status should handle UPSERT logic
            instance.update_article_status = AsyncMock(return_value=None)

            await button.callback(interaction)

            # Verify update_article_status was called (handles UPSERT internally)
            instance.update_article_status.assert_called_once()
            assert button.disabled is True


# ---------------------------------------------------------------------------
# Task 4.6.5 — RatingSelect 更新評分
# ---------------------------------------------------------------------------


class TestRatingSelectUpdateRating:
    @pytest.mark.asyncio
    async def test_rating_update_success(self):
        """RatingSelect successfully updates article rating."""
        item = make_reading_list_item()
        select = RatingSelect(item, row=2)
        select._values = ["4"]  # User selected 4 stars
        interaction = make_interaction()

        with patch("app.bot.cogs.reading_list.SupabaseService") as MockSupabase:
            instance = MockSupabase.return_value
            instance.update_article_rating = AsyncMock(return_value=None)

            await select.callback(interaction)

            # Verify update_article_rating was called with correct parameters
            instance.update_article_rating.assert_called_once_with(
                str(interaction.user.id), item.article_id, 4
            )

            # Verify confirmation message contains stars
            interaction.followup.send.assert_called_once()
            call_args = interaction.followup.send.call_args
            sent_content = call_args[0][0]
            assert "⭐" in sent_content
            assert "4 星" in sent_content
            assert call_args[1]["ephemeral"] is True


# ---------------------------------------------------------------------------
# Task 4.6.6 — RatingSelect 驗證評分範圍
# ---------------------------------------------------------------------------


class TestRatingSelectValidation:
    def test_rating_options_are_1_to_5(self):
        """RatingSelect options are exactly 1-5 stars."""
        item = make_reading_list_item()
        select = RatingSelect(item, row=2)

        option_values = {opt.value for opt in select.options}
        expected_values = {"1", "2", "3", "4", "5"}
        assert option_values == expected_values

    def test_rating_labels_show_stars(self):
        """RatingSelect option labels show star symbols."""
        item = make_reading_list_item()
        select = RatingSelect(item, row=2)

        for opt in select.options:
            assert "⭐" in opt.label


# ---------------------------------------------------------------------------
# Task 4.6.7 — custom_id 解析
# ---------------------------------------------------------------------------


class TestCustomIdParsing:
    def test_read_later_button_custom_id_format(self):
        """ReadLaterButton custom_id follows format 'read_later_{uuid}'."""
        article_id = uuid4()
        button = ReadLaterButton(article_id, "Test Article")

        assert button.custom_id == f"read_later_{article_id}"
        # Verify UUID can be extracted
        extracted_uuid = UUID(button.custom_id.replace("read_later_", ""))
        assert extracted_uuid == article_id

    def test_mark_read_button_custom_id_format(self):
        """MarkReadButton custom_id follows format 'mark_read_{uuid}'."""
        article_id = uuid4()
        button = MarkReadButton(article_id, "Test Article")

        assert button.custom_id == f"mark_read_{article_id}"
        # Verify UUID can be extracted
        extracted_uuid = UUID(button.custom_id.replace("mark_read_", ""))
        assert extracted_uuid == article_id

    def test_mark_as_read_button_custom_id_format(self):
        """MarkAsReadButton (reading list) custom_id follows format 'mark_read_{uuid}'."""
        item = make_reading_list_item()
        button = MarkAsReadButton(item, row=1)

        assert button.custom_id == f"mark_read_{item.article_id}"
        # Verify UUID can be extracted
        extracted_uuid = UUID(button.custom_id.replace("mark_read_", ""))
        assert extracted_uuid == item.article_id

    def test_rating_select_custom_id_format(self):
        """RatingSelect custom_id follows format 'rate_{uuid}'."""
        item = make_reading_list_item()
        select = RatingSelect(item, row=2)

        assert select.custom_id == f"rate_{item.article_id}"
        # Verify UUID can be extracted
        extracted_uuid = UUID(select.custom_id.replace("rate_", ""))
        assert extracted_uuid == item.article_id


# ---------------------------------------------------------------------------
# Task 4.6.8 — 按鈕禁用
# ---------------------------------------------------------------------------


class TestButtonDisabling:
    @pytest.mark.asyncio
    async def test_read_later_button_disabled_after_success(self):
        """ReadLaterButton is disabled after successful save."""
        article_id = uuid4()
        button = ReadLaterButton(article_id, "Test Article")
        interaction = make_interaction()

        with patch("app.bot.cogs.interactions.SupabaseService") as MockSupabase:
            instance = MockSupabase.return_value
            instance.save_to_reading_list = AsyncMock(return_value=None)

            assert button.disabled is False  # Initially enabled
            await button.callback(interaction)
            assert button.disabled is True  # Disabled after success

    @pytest.mark.asyncio
    async def test_mark_read_button_disabled_after_success(self):
        """MarkReadButton is disabled after successful update."""
        article_id = uuid4()
        button = MarkReadButton(article_id, "Test Article")
        interaction = make_interaction()

        with patch("app.bot.cogs.interactions.SupabaseService") as MockSupabase:
            instance = MockSupabase.return_value
            instance.update_article_status = AsyncMock(return_value=None)

            assert button.disabled is False  # Initially enabled
            await button.callback(interaction)
            assert button.disabled is True  # Disabled after success


# ---------------------------------------------------------------------------
# Task 4.6.9 — 錯誤處理
# ---------------------------------------------------------------------------


class TestButtonErrorHandling:
    @pytest.mark.asyncio
    async def test_read_later_button_error_handling(self):
        """ReadLaterButton handles errors gracefully and shows error message."""
        article_id = uuid4()
        button = ReadLaterButton(article_id, "Test Article")
        interaction = make_interaction()

        with patch("app.bot.cogs.interactions.SupabaseService") as MockSupabase:
            instance = MockSupabase.return_value
            instance.save_to_reading_list = AsyncMock(
                side_effect=Exception("Database connection failed")
            )

            await button.callback(interaction)

            # Button should NOT be disabled on error
            assert button.disabled is False

            # Error message should be sent
            interaction.followup.send.assert_called_once()
            call_args = interaction.followup.send.call_args
            assert "❌" in call_args[0][0]
            assert call_args[1]["ephemeral"] is True

    @pytest.mark.asyncio
    async def test_mark_read_button_error_handling(self):
        """MarkReadButton handles errors gracefully and shows error message."""
        article_id = uuid4()
        button = MarkReadButton(article_id, "Test Article")
        interaction = make_interaction()

        with patch("app.bot.cogs.interactions.SupabaseService") as MockSupabase:
            instance = MockSupabase.return_value
            instance.update_article_status = AsyncMock(
                side_effect=SupabaseServiceError("Update failed")
            )

            await button.callback(interaction)

            # Button should NOT be disabled on error
            assert button.disabled is False

            # Error message should be sent
            interaction.followup.send.assert_called_once()
            call_args = interaction.followup.send.call_args
            assert "❌" in call_args[0][0]
            assert call_args[1]["ephemeral"] is True

    @pytest.mark.asyncio
    async def test_rating_select_error_handling(self):
        """RatingSelect handles errors gracefully and shows error message."""
        item = make_reading_list_item()
        select = RatingSelect(item, row=2)
        select._values = ["5"]
        interaction = make_interaction()

        with patch("app.bot.cogs.reading_list.SupabaseService") as MockSupabase:
            instance = MockSupabase.return_value
            instance.update_article_rating = AsyncMock(
                side_effect=Exception("Rating update failed")
            )

            await select.callback(interaction)

            # Error message should be sent
            interaction.followup.send.assert_called_once()
            call_args = interaction.followup.send.call_args
            assert "❌" in call_args[0][0]
            assert call_args[1]["ephemeral"] is True


# ---------------------------------------------------------------------------
# Task 4.6.10 — MarkAsReadButton (reading list) 測試
# ---------------------------------------------------------------------------


class TestMarkAsReadButtonReadingList:
    @pytest.mark.asyncio
    async def test_mark_as_read_button_success(self):
        """MarkAsReadButton (reading list) successfully marks article as read."""
        item = make_reading_list_item()
        button = MarkAsReadButton(item, row=1)
        interaction = make_interaction()

        with patch("app.bot.cogs.reading_list.SupabaseService") as MockSupabase:
            instance = MockSupabase.return_value
            instance.update_article_status = AsyncMock(return_value=None)

            await button.callback(interaction)

            # Verify update_article_status was called
            instance.update_article_status.assert_called_once_with(
                str(interaction.user.id), item.article_id, "Read"
            )

            # Verify button was disabled
            assert button.disabled is True

            # Verify confirmation message
            interaction.followup.send.assert_called_once()
            call_args = interaction.followup.send.call_args
            assert "✅" in call_args[0][0]
            assert call_args[1]["ephemeral"] is True

    @pytest.mark.asyncio
    async def test_mark_as_read_button_error_keeps_button_enabled(self):
        """MarkAsReadButton does NOT disable on error."""
        item = make_reading_list_item()
        button = MarkAsReadButton(item, row=1)
        interaction = make_interaction()

        with patch("app.bot.cogs.reading_list.SupabaseService") as MockSupabase:
            instance = MockSupabase.return_value
            instance.update_article_status = AsyncMock(side_effect=Exception("Database error"))

            await button.callback(interaction)

            # Button should remain enabled on error
            assert button.disabled is False

            # Error message should be sent
            interaction.followup.send.assert_called_once()
            call_args = interaction.followup.send.call_args
            assert "❌" in call_args[0][0]
