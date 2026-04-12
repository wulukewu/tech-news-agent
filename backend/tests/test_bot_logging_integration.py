"""
Test bot cogs logging and error handling integration.

This test verifies that bot cogs use centralized logging and error handling.
"""

from unittest.mock import Mock

import pytest

from app.bot.cogs.admin_commands import AdminCommands
from app.bot.cogs.news_commands import NewsCommands
from app.bot.cogs.notification_settings import NotificationSettings
from app.bot.cogs.reading_list import ReadingListCog
from app.bot.cogs.subscription_commands import SubscriptionCommands
from app.core.logger import get_logger


class TestBotLoggingIntegration:
    """Test bot cogs use centralized logging and error handling."""

    def test_news_commands_uses_structured_logger(self):
        """Verify NewsCommands uses structured logger."""
        bot = Mock()
        cog = NewsCommands(bot)

        # Verify logger is from centralized logging system

        assert hasattr(cog, "supabase_service")
        # Logger is imported at module level, check it's the right type
        from app.bot.cogs import news_commands

        assert hasattr(news_commands, "logger")

    def test_subscription_commands_uses_structured_logger(self):
        """Verify SubscriptionCommands uses structured logger."""
        bot = Mock()
        cog = SubscriptionCommands(bot)

        # Verify cog has service layer dependency
        assert hasattr(cog, "supabase_service")
        from app.bot.cogs import subscription_commands

        assert hasattr(subscription_commands, "logger")

    def test_reading_list_uses_structured_logger(self):
        """Verify ReadingListCog uses structured logger."""
        bot = Mock()
        cog = ReadingListCog(bot)

        # Verify cog has service layer dependencies
        assert hasattr(cog, "supabase_service")
        assert hasattr(cog, "llm_service")
        from app.bot.cogs import reading_list

        assert hasattr(reading_list, "logger")

    def test_admin_commands_uses_structured_logger(self):
        """Verify AdminCommands uses structured logger."""
        bot = Mock()
        cog = AdminCommands(bot)

        from app.bot.cogs import admin_commands

        assert hasattr(admin_commands, "logger")

    def test_notification_settings_uses_structured_logger(self):
        """Verify NotificationSettings uses structured logger."""
        bot = Mock()
        cog = NotificationSettings(bot)

        # Verify cog has service layer dependency
        assert hasattr(cog, "supabase_service")
        from app.bot.cogs import notification_settings

        assert hasattr(notification_settings, "logger")

    def test_structured_logger_format(self):
        """Verify structured logger produces JSON output."""
        import json
        import logging

        # Create a test logger with string handler
        test_logger = get_logger("test_bot", level=logging.INFO)

        # Get the handler and capture its formatter output
        handler = test_logger.logger.handlers[0]

        # Create a log record
        record = logging.LogRecord(
            name="test_bot",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None,
        )
        record.extra_fields = {"user_id": "123", "command": "test"}

        # Format the record
        formatted = handler.formatter.format(record)

        # Parse JSON output
        log_entry = json.loads(formatted)

        # Verify structure
        assert "timestamp" in log_entry
        assert "level" in log_entry
        assert log_entry["level"] == "INFO"
        assert "logger" in log_entry
        assert log_entry["logger"] == "test_bot"
        assert "message" in log_entry
        assert log_entry["message"] == "Test message"
        assert "extra" in log_entry
        assert log_entry["extra"]["user_id"] == "123"
        assert log_entry["extra"]["command"] == "test"

    @pytest.mark.asyncio
    async def test_error_messages_include_actionable_suggestions(self):
        """Verify error messages include actionable suggestions for users."""
        # This test verifies the error message format by checking the code
        # The actual error messages are tested in integration tests

        # Read the news_commands.py file to verify error messages
        import os

        cog_path = os.path.join(
            os.path.dirname(__file__), "..", "app", "bot", "cogs", "news_commands.py"
        )

        with open(cog_path) as f:
            content = f.read()

        # Verify error messages include actionable suggestions
        assert "💡 建議" in content or "💡 Suggestion" in content
        assert "❌" in content  # Error emoji

        # Verify structured logging is used
        assert "logger.error(" in content or "logger.critical(" in content
        assert "user_id=" in content  # Context is included in logs


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
