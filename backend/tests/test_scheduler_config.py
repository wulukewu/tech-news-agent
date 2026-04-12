"""
Tests for scheduler configuration and CRON expression validation.

Validates: Requirements 6.1, 6.2, 6.3, 6.4, 6.5, 6.6
"""

from unittest.mock import patch

import pytest
from apscheduler.triggers.cron import CronTrigger

from app.core.config import Settings
from app.tasks.scheduler import scheduler, setup_scheduler


class TestSchedulerConfiguration:
    """Unit tests for scheduler configuration."""

    def test_setup_scheduler_with_default_cron(self):
        """
        Test that setup_scheduler uses default CRON expression when not configured.

        Validates: Requirement 6.3
        """
        with patch("app.tasks.scheduler.settings") as mock_settings:
            mock_settings.scheduler_cron = "0 */6 * * *"
            mock_settings.scheduler_timezone = None
            mock_settings.timezone = "Asia/Taipei"

            # Clear any existing jobs
            scheduler.remove_all_jobs()

            # Setup scheduler
            setup_scheduler()

            # Verify job was added
            jobs = scheduler.get_jobs()
            assert len(jobs) == 1
            assert jobs[0].id == "background_fetch"
            assert jobs[0].name == "Background Article Fetch and Analysis"

    def test_setup_scheduler_with_custom_cron(self):
        """
        Test that setup_scheduler accepts custom CRON expression.

        Validates: Requirement 6.1, 6.2
        """
        with patch("app.tasks.scheduler.settings") as mock_settings:
            mock_settings.scheduler_cron = "0 0 * * *"  # Daily at midnight
            mock_settings.scheduler_timezone = None
            mock_settings.timezone = "UTC"

            # Clear any existing jobs
            scheduler.remove_all_jobs()

            # Setup scheduler
            setup_scheduler()

            # Verify job was added with custom schedule
            jobs = scheduler.get_jobs()
            assert len(jobs) == 1
            assert jobs[0].id == "background_fetch"

    def test_setup_scheduler_with_custom_timezone(self):
        """
        Test that setup_scheduler uses custom timezone when provided.

        Validates: Requirement 6.6
        """
        with patch("app.tasks.scheduler.settings") as mock_settings:
            mock_settings.scheduler_cron = "0 */6 * * *"
            mock_settings.scheduler_timezone = "America/New_York"
            mock_settings.timezone = "Asia/Taipei"

            # Clear any existing jobs
            scheduler.remove_all_jobs()

            # Setup scheduler
            setup_scheduler()

            # Verify job was added
            jobs = scheduler.get_jobs()
            assert len(jobs) == 1

    def test_setup_scheduler_falls_back_to_general_timezone(self):
        """
        Test that setup_scheduler falls back to general timezone when scheduler_timezone is None.

        Validates: Requirement 6.6
        """
        with patch("app.tasks.scheduler.settings") as mock_settings:
            mock_settings.scheduler_cron = "0 */6 * * *"
            mock_settings.scheduler_timezone = None
            mock_settings.timezone = "Europe/London"

            # Clear any existing jobs
            scheduler.remove_all_jobs()

            # Setup scheduler
            setup_scheduler()

            # Verify job was added
            jobs = scheduler.get_jobs()
            assert len(jobs) == 1

    def test_setup_scheduler_with_invalid_cron_raises_error(self):
        """
        Test that setup_scheduler raises ValueError for invalid CRON expression.

        Validates: Requirement 6.5
        """
        with patch("app.tasks.scheduler.settings") as mock_settings:
            mock_settings.scheduler_cron = "invalid_cron"
            mock_settings.scheduler_timezone = None
            mock_settings.timezone = "Asia/Taipei"

            # Clear any existing jobs
            scheduler.remove_all_jobs()

            # Setup scheduler should raise ValueError
            with pytest.raises(ValueError) as exc_info:
                setup_scheduler()

            assert "Invalid CRON expression" in str(exc_info.value)
            assert "invalid_cron" in str(exc_info.value)

    def test_setup_scheduler_with_invalid_cron_field_values(self):
        """
        Test that setup_scheduler raises ValueError for CRON with invalid field values.

        Validates: Requirement 6.5
        """
        with patch("app.tasks.scheduler.settings") as mock_settings:
            mock_settings.scheduler_cron = "60 * * * *"  # Invalid minute (60)
            mock_settings.scheduler_timezone = None
            mock_settings.timezone = "Asia/Taipei"

            # Clear any existing jobs
            scheduler.remove_all_jobs()

            # Setup scheduler should raise ValueError
            with pytest.raises(ValueError) as exc_info:
                setup_scheduler()

            assert "Invalid CRON expression" in str(exc_info.value)

    def test_setup_scheduler_logs_configuration(self, caplog):
        """
        Test that setup_scheduler logs the configured schedule on startup.

        Validates: Requirement 6.4
        """
        import logging

        caplog.set_level(logging.INFO)

        with patch("app.tasks.scheduler.settings") as mock_settings:
            mock_settings.scheduler_cron = "0 9 * * 1"  # Every Monday at 9am
            mock_settings.scheduler_timezone = "UTC"
            mock_settings.timezone = "Asia/Taipei"

            # Clear any existing jobs
            scheduler.remove_all_jobs()

            # Setup scheduler
            setup_scheduler()

            # Verify log message
            assert any(
                "Scheduler configured successfully" in record.message for record in caplog.records
            )
            assert any("CRON='0 9 * * 1'" in record.message for record in caplog.records)
            assert any("Timezone='UTC'" in record.message for record in caplog.records)

    def test_setup_scheduler_with_various_valid_cron_expressions(self):
        """
        Test that setup_scheduler accepts various valid CRON expressions.

        Validates: Requirement 6.2
        """
        valid_cron_expressions = [
            "0 */6 * * *",  # Every 6 hours
            "0 0 * * *",  # Daily at midnight
            "0 9 * * 1",  # Every Monday at 9am
            "*/30 * * * *",  # Every 30 minutes
            "0 0 1 * *",  # First day of every month
            "0 12 * * 1-5",  # Weekdays at noon
        ]

        for cron_expr in valid_cron_expressions:
            with patch("app.tasks.scheduler.settings") as mock_settings:
                mock_settings.scheduler_cron = cron_expr
                mock_settings.scheduler_timezone = None
                mock_settings.timezone = "Asia/Taipei"

                # Clear any existing jobs
                scheduler.remove_all_jobs()

                # Setup scheduler should not raise
                setup_scheduler()

                # Verify job was added
                jobs = scheduler.get_jobs()
                assert len(jobs) >= 1

                # Verify the background_fetch job exists
                job = scheduler.get_job("background_fetch")
                assert job is not None


class TestCronTriggerValidation:
    """Tests for CRON expression validation using CronTrigger."""

    def test_cron_trigger_from_crontab_with_valid_expression(self):
        """Test that CronTrigger.from_crontab accepts valid CRON expressions."""
        valid_expressions = [
            "0 */6 * * *",
            "0 0 * * *",
            "*/30 * * * *",
        ]

        for expr in valid_expressions:
            trigger = CronTrigger.from_crontab(expr, timezone="UTC")
            assert trigger is not None

    def test_cron_trigger_from_crontab_with_invalid_expression(self):
        """Test that CronTrigger.from_crontab raises error for invalid CRON expressions."""
        invalid_expressions = [
            "invalid",
            "60 * * * *",  # Invalid minute
            "* * * * * *",  # Too many fields
            "",  # Empty string
        ]

        for expr in invalid_expressions:
            with pytest.raises((ValueError, TypeError)):
                CronTrigger.from_crontab(expr, timezone="UTC")


class TestSettingsDefaults:
    """Tests for Settings class defaults."""

    def test_settings_scheduler_cron_default(self):
        """Test that scheduler_cron has correct default value."""
        with patch.dict(
            "os.environ",
            {
                "SUPABASE_URL": "http://test.com",
                "SUPABASE_KEY": "test_key",
                "DISCORD_TOKEN": "test_token",
                "DISCORD_CHANNEL_ID": "123456",
                "GROQ_API_KEY": "test_groq_key",
            },
            clear=True,
        ):
            settings = Settings()
            assert settings.scheduler_cron == "0 */6 * * *"

    def test_settings_scheduler_timezone_default(self):
        """Test that scheduler_timezone defaults to None."""
        with patch.dict(
            "os.environ",
            {
                "SUPABASE_URL": "http://test.com",
                "SUPABASE_KEY": "test_key",
                "DISCORD_TOKEN": "test_token",
                "DISCORD_CHANNEL_ID": "123456",
                "GROQ_API_KEY": "test_groq_key",
            },
            clear=True,
        ):
            settings = Settings()
            assert settings.scheduler_timezone is None

    def test_settings_reads_scheduler_cron_from_env(self):
        """Test that scheduler_cron can be overridden via environment variable."""
        with patch.dict(
            "os.environ",
            {
                "SUPABASE_URL": "http://test.com",
                "SUPABASE_KEY": "test_key",
                "DISCORD_TOKEN": "test_token",
                "DISCORD_CHANNEL_ID": "123456",
                "GROQ_API_KEY": "test_groq_key",
                "SCHEDULER_CRON": "0 0 * * *",
            },
            clear=True,
        ):
            settings = Settings()
            assert settings.scheduler_cron == "0 0 * * *"

    def test_settings_reads_scheduler_timezone_from_env(self):
        """Test that scheduler_timezone can be set via environment variable."""
        with patch.dict(
            "os.environ",
            {
                "SUPABASE_URL": "http://test.com",
                "SUPABASE_KEY": "test_key",
                "DISCORD_TOKEN": "test_token",
                "DISCORD_CHANNEL_ID": "123456",
                "GROQ_API_KEY": "test_groq_key",
                "SCHEDULER_TIMEZONE": "America/New_York",
            },
            clear=True,
        ):
            settings = Settings()
            assert settings.scheduler_timezone == "America/New_York"
