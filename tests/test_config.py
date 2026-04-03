"""
Unit tests for configuration module
Task 1.4: 撰寫配置模組的單元測試
Requirements: 1.1, 1.2, 1.3, 1.4
"""
import pytest
from unittest.mock import patch
import os
import sys
from importlib import reload


class TestConfigurationModule:
    """Test configuration module structure and behavior."""
    
    def test_settings_has_supabase_url_field(self):
        """Settings class contains supabase_url field."""
        # Import only the class, not the instantiated settings object
        import app.core.config as config_module
        Settings = config_module.Settings
        
        # Check that the field exists in the model
        assert 'supabase_url' in Settings.model_fields
        # Verify it's a required string field
        field_info = Settings.model_fields['supabase_url']
        assert field_info.annotation == str
    
    def test_settings_has_supabase_key_field(self):
        """Settings class contains supabase_key field."""
        import app.core.config as config_module
        Settings = config_module.Settings
        
        # Check that the field exists in the model
        assert 'supabase_key' in Settings.model_fields
        # Verify it's a required string field
        field_info = Settings.model_fields['supabase_key']
        assert field_info.annotation == str
    
    def test_settings_does_not_have_notion_token_field(self):
        """Settings class does not contain notion_token field."""
        import app.core.config as config_module
        Settings = config_module.Settings
        
        assert 'notion_token' not in Settings.model_fields
    
    def test_settings_does_not_have_notion_feeds_db_id_field(self):
        """Settings class does not contain notion_feeds_db_id field."""
        import app.core.config as config_module
        Settings = config_module.Settings
        
        assert 'notion_feeds_db_id' not in Settings.model_fields
    
    def test_settings_does_not_have_notion_read_later_db_id_field(self):
        """Settings class does not contain notion_read_later_db_id field."""
        import app.core.config as config_module
        Settings = config_module.Settings
        
        assert 'notion_read_later_db_id' not in Settings.model_fields
    
    def test_settings_does_not_have_notion_weekly_digests_db_id_field(self):
        """Settings class does not contain notion_weekly_digests_db_id field."""
        import app.core.config as config_module
        Settings = config_module.Settings
        
        assert 'notion_weekly_digests_db_id' not in Settings.model_fields
    
    def test_settings_does_not_have_any_notion_fields(self):
        """Settings class does not contain any notion_* fields."""
        import app.core.config as config_module
        Settings = config_module.Settings
        
        # Get all field names
        field_names = Settings.model_fields.keys()
        
        # Check that no field starts with 'notion_'
        notion_fields = [field for field in field_names if field.startswith('notion_')]
        assert len(notion_fields) == 0, f"Found unexpected notion fields: {notion_fields}"
    
    def test_settings_loads_from_environment_variables(self):
        """Settings loads configuration from environment variables."""
        import app.core.config as config_module
        Settings = config_module.Settings
        
        # Mock environment variables
        test_env = {
            'SUPABASE_URL': 'https://test-project.supabase.co',
            'SUPABASE_KEY': 'test-anon-key-12345',
            'DISCORD_TOKEN': 'test-discord-token',
            'DISCORD_CHANNEL_ID': '123456789',
            'GROQ_API_KEY': 'test-groq-key'
        }
        
        with patch.dict(os.environ, test_env, clear=False):
            # Create a new instance
            settings = Settings()
            
            # Verify values are loaded correctly
            assert settings.supabase_url == 'https://test-project.supabase.co'
            assert settings.supabase_key == 'test-anon-key-12345'
            assert settings.discord_token == 'test-discord-token'
            assert settings.discord_channel_id == 123456789
            assert settings.groq_api_key == 'test-groq-key'
    
    def test_settings_requires_supabase_url(self):
        """Settings raises validation error when SUPABASE_URL is missing."""
        from pydantic import ValidationError
        import app.core.config as config_module
        Settings = config_module.Settings
        
        # Mock environment with missing SUPABASE_URL
        # We need to prevent reading from .env file
        test_env = {
            'SUPABASE_KEY': 'test-key',
            'DISCORD_TOKEN': 'test-token',
            'DISCORD_CHANNEL_ID': '123456789',
            'GROQ_API_KEY': 'test-groq-key'
        }
        
        with patch.dict(os.environ, test_env, clear=True):
            # Create Settings with _env_file=None to prevent reading from .env
            with pytest.raises(ValidationError) as exc_info:
                Settings(_env_file=None)
            
            # Check that the error mentions supabase_url
            error_str = str(exc_info.value)
            assert 'supabase_url' in error_str.lower()
    
    def test_settings_requires_supabase_key(self):
        """Settings raises validation error when SUPABASE_KEY is missing."""
        from pydantic import ValidationError
        import app.core.config as config_module
        Settings = config_module.Settings
        
        # Mock environment with missing SUPABASE_KEY
        # We need to prevent reading from .env file
        test_env = {
            'SUPABASE_URL': 'https://test.supabase.co',
            'DISCORD_TOKEN': 'test-token',
            'DISCORD_CHANNEL_ID': '123456789',
            'GROQ_API_KEY': 'test-groq-key'
        }
        
        with patch.dict(os.environ, test_env, clear=True):
            # Create Settings with _env_file=None to prevent reading from .env
            with pytest.raises(ValidationError) as exc_info:
                Settings(_env_file=None)
            
            # Check that the error mentions supabase_key
            error_str = str(exc_info.value)
            assert 'supabase_key' in error_str.lower()
    
    def test_settings_has_default_timezone(self):
        """Settings has default timezone value of Asia/Taipei."""
        import app.core.config as config_module
        Settings = config_module.Settings
        
        # Check the default value
        field_info = Settings.model_fields['timezone']
        assert field_info.default == 'Asia/Taipei'
    
    def test_settings_preserves_existing_fields(self):
        """Settings preserves all existing non-Notion fields."""
        import app.core.config as config_module
        Settings = config_module.Settings
        
        # Verify that existing fields are still present
        required_fields = [
            'supabase_url',
            'supabase_key',
            'discord_token',
            'discord_channel_id',
            'groq_api_key',
            'timezone'
        ]
        
        for field in required_fields:
            assert field in Settings.model_fields, f"Missing required field: {field}"
