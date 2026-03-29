"""
Unit tests for startup configuration validation
Task 1.2: Verify ConfigurationError is raised when notion_weekly_digests_db_id is empty
"""
import pytest
from unittest.mock import patch

from app.core.exceptions import ConfigurationError


class TestStartupValidation:
    """Test startup configuration validation."""
    
    def test_validate_configuration_succeeds_with_valid_db_id(self):
        """validate_configuration succeeds when notion_weekly_digests_db_id is set."""
        # Import here to get fresh module state
        from app.main import validate_configuration
        from app.core.config import settings
        
        # Since settings is already loaded with valid values from .env, this should pass
        validate_configuration()
    
    def test_validate_configuration_raises_error_when_db_id_is_empty_string(self):
        """validate_configuration raises ConfigurationError when notion_weekly_digests_db_id is empty string."""
        # We need to patch at the point of use, not at import time
        with patch("app.main.settings") as mock_settings:
            mock_settings.notion_weekly_digests_db_id = ""
            
            # Import the function after patching
            from app.main import validate_configuration
            
            with pytest.raises(ConfigurationError) as exc_info:
                validate_configuration()
            
            assert "NOTION_WEEKLY_DIGESTS_DB_ID" in str(exc_info.value)
            assert "required" in str(exc_info.value).lower()
    
    def test_validate_configuration_raises_error_when_db_id_is_none(self):
        """validate_configuration raises ConfigurationError when notion_weekly_digests_db_id is None."""
        with patch("app.main.settings") as mock_settings:
            mock_settings.notion_weekly_digests_db_id = None
            
            from app.main import validate_configuration
            
            with pytest.raises(ConfigurationError) as exc_info:
                validate_configuration()
            
            assert "NOTION_WEEKLY_DIGESTS_DB_ID" in str(exc_info.value)
            assert "required" in str(exc_info.value).lower()
    
    def test_validate_configuration_raises_error_when_db_id_is_whitespace(self):
        """validate_configuration raises ConfigurationError when notion_weekly_digests_db_id is only whitespace."""
        with patch("app.main.settings") as mock_settings:
            mock_settings.notion_weekly_digests_db_id = "   "
            
            from app.main import validate_configuration
            
            with pytest.raises(ConfigurationError) as exc_info:
                validate_configuration()
            
            assert "NOTION_WEEKLY_DIGESTS_DB_ID" in str(exc_info.value)
            assert "required" in str(exc_info.value).lower()
