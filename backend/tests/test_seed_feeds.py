"""
Unit tests for seed_feeds.py script
Task 4.4: 撰寫種子腳本的單元測試
Requirements: 4.8, 4.9, 10.3, 10.5

These tests verify that the seed_feeds.py script:
- Raises errors when environment variables are missing
- Handles duplicate URL errors gracefully
- Handles connection failures with descriptive error messages
"""

import os
import sys
from unittest.mock import MagicMock, patch

import pytest
from supabase import Client

# Add scripts directory to path
scripts_path = os.path.join(os.path.dirname(__file__), "..", "scripts")
if scripts_path not in sys.path:
    sys.path.insert(0, scripts_path)


class TestSeedFeedsMissingEnvVars:
    """Test that seed script validates environment variables."""

    @patch("seed_feeds.load_dotenv")
    @patch("seed_feeds.os.getenv")
    def test_missing_supabase_url_raises_error(self, mock_getenv, mock_load_dotenv):
        """
        Verify that missing SUPABASE_URL raises a descriptive error.
        **Validates: Requirements 10.3**
        """

        # Mock environment variables - SUPABASE_URL is missing
        def getenv_side_effect(key, default=None):
            if key == "SUPABASE_URL":
                return None
            elif key == "SUPABASE_KEY":
                return "test-key"
            return default

        mock_getenv.side_effect = getenv_side_effect

        # Import and run the seed script
        import seed_feeds

        with pytest.raises(ValueError) as exc_info:
            seed_feeds.main()

        error_message = str(exc_info.value)
        assert "SUPABASE_URL" in error_message
        assert "Missing required environment variable" in error_message

    @patch("seed_feeds.load_dotenv")
    @patch("seed_feeds.os.getenv")
    def test_missing_supabase_key_raises_error(self, mock_getenv, mock_load_dotenv):
        """
        Verify that missing SUPABASE_KEY raises a descriptive error.
        **Validates: Requirements 10.3**
        """

        # Mock environment variables - SUPABASE_KEY is missing
        def getenv_side_effect(key, default=None):
            if key == "SUPABASE_URL":
                return "https://test.supabase.co"
            elif key == "SUPABASE_KEY":
                return None
            return default

        mock_getenv.side_effect = getenv_side_effect

        # Import and run the seed script
        import seed_feeds

        with pytest.raises(ValueError) as exc_info:
            seed_feeds.main()

        error_message = str(exc_info.value)
        assert "SUPABASE_KEY" in error_message
        assert "Missing required environment variable" in error_message

    @patch("seed_feeds.load_dotenv")
    @patch("seed_feeds.os.getenv")
    def test_missing_both_env_vars_raises_error(self, mock_getenv, mock_load_dotenv):
        """
        Verify that missing both environment variables raises an error.
        **Validates: Requirements 10.3**
        """

        # Mock environment variables - both are missing
        def getenv_side_effect(key, default=None):
            return None

        mock_getenv.side_effect = getenv_side_effect

        # Import and run the seed script
        import seed_feeds

        with pytest.raises(ValueError) as exc_info:
            seed_feeds.main()

        error_message = str(exc_info.value)
        # Should fail on the first check (SUPABASE_URL)
        assert "SUPABASE_URL" in error_message


class TestSeedFeedsDuplicateHandling:
    """Test that seed script handles duplicate URLs correctly."""

    @patch("seed_feeds.load_dotenv")
    @patch("seed_feeds.os.getenv")
    @patch("seed_feeds.create_client")
    def test_duplicate_url_is_skipped(
        self, mock_create_client, mock_getenv, mock_load_dotenv, capsys
    ):
        """
        Verify that duplicate feed URLs are skipped without crashing.
        **Validates: Requirements 4.8**
        """

        # Mock environment variables
        def getenv_side_effect(key, default=None):
            if key == "SUPABASE_URL":
                return "https://test.supabase.co"
            elif key == "SUPABASE_KEY":
                return "test-key"
            return default

        mock_getenv.side_effect = getenv_side_effect

        # Create mock Supabase client
        mock_client = MagicMock(spec=Client)
        mock_create_client.return_value = mock_client

        # Mock table operations
        mock_table = MagicMock()
        mock_client.table.return_value = mock_table

        # First insert succeeds, second raises duplicate error
        call_count = 0

        def insert_side_effect(data):
            nonlocal call_count
            call_count += 1
            mock_insert = MagicMock()
            if call_count == 2:  # Second call raises duplicate error
                mock_insert.execute.side_effect = Exception(
                    "duplicate key value violates unique constraint"
                )
            else:
                mock_insert.execute.return_value = MagicMock()
            return mock_insert

        mock_table.insert.side_effect = insert_side_effect

        # Run the seed script
        import seed_feeds

        seed_feeds.main()

        # Capture output
        captured = capsys.readouterr()

        # Verify that duplicate was skipped
        assert "Skipped (duplicate URL)" in captured.out
        assert "Seeding completed!" in captured.out

    @patch("seed_feeds.load_dotenv")
    @patch("seed_feeds.os.getenv")
    @patch("seed_feeds.create_client")
    def test_multiple_duplicates_are_all_skipped(
        self, mock_create_client, mock_getenv, mock_load_dotenv, capsys
    ):
        """
        Verify that multiple duplicate URLs are all skipped.
        **Validates: Requirements 4.8**
        """

        # Mock environment variables
        def getenv_side_effect(key, default=None):
            if key == "SUPABASE_URL":
                return "https://test.supabase.co"
            elif key == "SUPABASE_KEY":
                return "test-key"
            return default

        mock_getenv.side_effect = getenv_side_effect

        # Create mock Supabase client
        mock_client = MagicMock(spec=Client)
        mock_create_client.return_value = mock_client

        # Mock table operations - all inserts fail with duplicate error
        mock_table = MagicMock()
        mock_client.table.return_value = mock_table

        mock_insert = MagicMock()
        mock_insert.execute.side_effect = Exception(
            "duplicate key value violates unique constraint"
        )
        mock_table.insert.return_value = mock_insert

        # Run the seed script
        import seed_feeds

        seed_feeds.main()

        # Capture output
        captured = capsys.readouterr()

        # Verify that all duplicates were skipped
        assert captured.out.count("Skipped (duplicate URL)") > 0
        assert "Seeding completed!" in captured.out
        assert "Successfully inserted: 0 feeds" in captured.out


class TestSeedFeedsConnectionFailure:
    """Test that seed script handles connection failures gracefully."""

    @patch("seed_feeds.load_dotenv")
    @patch("seed_feeds.os.getenv")
    @patch("seed_feeds.create_client")
    def test_connection_failure_raises_descriptive_error(
        self, mock_create_client, mock_getenv, mock_load_dotenv
    ):
        """
        Verify that connection failures raise descriptive errors.
        **Validates: Requirements 4.9, 10.5**
        """

        # Mock environment variables
        def getenv_side_effect(key, default=None):
            if key == "SUPABASE_URL":
                return "https://test.supabase.co"
            elif key == "SUPABASE_KEY":
                return "test-key"
            return default

        mock_getenv.side_effect = getenv_side_effect

        # Mock create_client to raise connection error
        mock_create_client.side_effect = Exception("Connection refused")

        # Run the seed script
        import seed_feeds

        with pytest.raises(ConnectionError) as exc_info:
            seed_feeds.main()

        error_message = str(exc_info.value)
        assert "Failed to connect to Supabase" in error_message
        assert "SUPABASE_URL is correct" in error_message
        assert "SUPABASE_KEY is valid" in error_message

    @patch("seed_feeds.load_dotenv")
    @patch("seed_feeds.os.getenv")
    @patch("seed_feeds.create_client")
    def test_network_error_during_insert_raises_descriptive_error(
        self, mock_create_client, mock_getenv, mock_load_dotenv
    ):
        """
        Verify that network errors during insertion raise descriptive errors.
        **Validates: Requirements 10.5**
        """

        # Mock environment variables
        def getenv_side_effect(key, default=None):
            if key == "SUPABASE_URL":
                return "https://test.supabase.co"
            elif key == "SUPABASE_KEY":
                return "test-key"
            return default

        mock_getenv.side_effect = getenv_side_effect

        # Create mock Supabase client
        mock_client = MagicMock(spec=Client)
        mock_create_client.return_value = mock_client

        # Mock table operations to raise network error
        mock_table = MagicMock()
        mock_client.table.return_value = mock_table

        mock_insert = MagicMock()
        mock_insert.execute.side_effect = Exception("Network timeout error")
        mock_table.insert.return_value = mock_insert

        # Run the seed script
        import seed_feeds

        with pytest.raises(ConnectionError) as exc_info:
            seed_feeds.main()

        error_message = str(exc_info.value)
        assert "Network error" in error_message
        assert "internet connection" in error_message

    @patch("seed_feeds.load_dotenv")
    @patch("seed_feeds.os.getenv")
    @patch("seed_feeds.create_client")
    def test_invalid_credentials_raises_descriptive_error(
        self, mock_create_client, mock_getenv, mock_load_dotenv
    ):
        """
        Verify that invalid credentials raise descriptive errors.
        **Validates: Requirements 4.9**
        """

        # Mock environment variables
        def getenv_side_effect(key, default=None):
            if key == "SUPABASE_URL":
                return "https://test.supabase.co"
            elif key == "SUPABASE_KEY":
                return "invalid-key"
            return default

        mock_getenv.side_effect = getenv_side_effect

        # Mock create_client to raise authentication error
        mock_create_client.side_effect = Exception("Invalid API key")

        # Run the seed script
        import seed_feeds

        with pytest.raises(ConnectionError) as exc_info:
            seed_feeds.main()

        error_message = str(exc_info.value)
        assert "Failed to connect to Supabase" in error_message


class TestSeedFeedsSuccessfulExecution:
    """Test successful execution of seed script."""

    @patch("seed_feeds.load_dotenv")
    @patch("seed_feeds.os.getenv")
    @patch("seed_feeds.create_client")
    def test_successful_seed_prints_summary(
        self, mock_create_client, mock_getenv, mock_load_dotenv, capsys
    ):
        """
        Verify that successful seeding prints the number of feeds inserted.
        **Validates: Requirements 4.10**
        """

        # Mock environment variables
        def getenv_side_effect(key, default=None):
            if key == "SUPABASE_URL":
                return "https://test.supabase.co"
            elif key == "SUPABASE_KEY":
                return "test-key"
            return default

        mock_getenv.side_effect = getenv_side_effect

        # Create mock Supabase client
        mock_client = MagicMock(spec=Client)
        mock_create_client.return_value = mock_client

        # Mock table operations - all inserts succeed
        mock_table = MagicMock()
        mock_client.table.return_value = mock_table

        mock_insert = MagicMock()
        mock_insert.execute.return_value = MagicMock()
        mock_table.insert.return_value = mock_insert

        # Run the seed script
        import seed_feeds

        seed_feeds.main()

        # Capture output
        captured = capsys.readouterr()

        # Verify summary is printed
        assert "Seeding completed!" in captured.out
        assert "Successfully inserted:" in captured.out
        assert "feeds" in captured.out

    @patch("seed_feeds.load_dotenv")
    @patch("seed_feeds.os.getenv")
    @patch("seed_feeds.create_client")
    def test_mixed_success_and_duplicates_prints_both_counts(
        self, mock_create_client, mock_getenv, mock_load_dotenv, capsys
    ):
        """
        Verify that mixed results print both inserted and skipped counts.
        **Validates: Requirements 4.8, 4.10**
        """

        # Mock environment variables
        def getenv_side_effect(key, default=None):
            if key == "SUPABASE_URL":
                return "https://test.supabase.co"
            elif key == "SUPABASE_KEY":
                return "test-key"
            return default

        mock_getenv.side_effect = getenv_side_effect

        # Create mock Supabase client
        mock_client = MagicMock(spec=Client)
        mock_create_client.return_value = mock_client

        # Mock table operations - some succeed, some are duplicates
        mock_table = MagicMock()
        mock_client.table.return_value = mock_table

        call_count = 0

        def insert_side_effect(data):
            nonlocal call_count
            call_count += 1
            mock_insert = MagicMock()
            # Every other call is a duplicate
            if call_count % 2 == 0:
                mock_insert.execute.side_effect = Exception(
                    "duplicate key value violates unique constraint"
                )
            else:
                mock_insert.execute.return_value = MagicMock()
            return mock_insert

        mock_table.insert.side_effect = insert_side_effect

        # Run the seed script
        import seed_feeds

        seed_feeds.main()

        # Capture output
        captured = capsys.readouterr()

        # Verify both counts are printed
        assert "Successfully inserted:" in captured.out
        assert "Skipped (duplicates):" in captured.out
        assert "Seeding completed!" in captured.out
