"""
Integration tests for scheduler configuration.

These tests verify that the scheduler can be initialized and configured
with real environment variables.

Validates: Requirements 6.1, 6.2, 6.3, 6.4, 6.5, 6.6
"""

import pytest
import os
from unittest.mock import patch

from app.tasks.scheduler import setup_scheduler, scheduler


class TestSchedulerIntegration:
    """Integration tests for scheduler with real configuration."""
    
    def test_scheduler_initialization_with_env_vars(self):
        """
        Test that scheduler can be initialized with environment variables.
        
        Validates: Requirements 6.1, 6.2, 6.3
        """
        # Set environment variables
        test_env = {
            'SCHEDULER_CRON': '0 0 * * *',
            'SCHEDULER_TIMEZONE': 'UTC',
        }
        
        with patch.dict(os.environ, test_env):
            # Reload settings to pick up new env vars
            from importlib import reload
            from app.core import config
            reload(config)
            
            with patch('app.tasks.scheduler.settings', config.settings):
                # Clear any existing jobs
                scheduler.remove_all_jobs()
                
                # Setup scheduler
                setup_scheduler()
                
                # Verify job was added
                job = scheduler.get_job('background_fetch')
                assert job is not None
                assert job.name == 'Background Article Fetch and Analysis'
    
    def test_scheduler_fails_fast_on_invalid_cron(self):
        """
        Test that scheduler raises error on startup with invalid CRON.
        
        Validates: Requirement 6.5
        """
        test_env = {
            'SCHEDULER_CRON': 'not_a_valid_cron',
        }
        
        with patch.dict(os.environ, test_env):
            # Reload settings to pick up new env vars
            from importlib import reload
            from app.core import config
            reload(config)
            
            with patch('app.tasks.scheduler.settings', config.settings):
                # Clear any existing jobs
                scheduler.remove_all_jobs()
                
                # Setup scheduler should raise ValueError
                with pytest.raises(ValueError) as exc_info:
                    setup_scheduler()
                
                assert "Invalid CRON expression" in str(exc_info.value)
    
    def test_scheduler_uses_default_values(self):
        """
        Test that scheduler uses default values when env vars not set.
        
        Validates: Requirement 6.3
        """
        # Remove scheduler env vars if they exist
        test_env = os.environ.copy()
        test_env.pop('SCHEDULER_CRON', None)
        test_env.pop('SCHEDULER_TIMEZONE', None)
        
        with patch.dict(os.environ, test_env, clear=False):
            # Reload settings to pick up defaults
            from importlib import reload
            from app.core import config
            reload(config)
            
            # Verify defaults
            assert config.settings.scheduler_cron == "0 */6 * * *"
            assert config.settings.scheduler_timezone is None
            
            with patch('app.tasks.scheduler.settings', config.settings):
                # Clear any existing jobs
                scheduler.remove_all_jobs()
                
                # Setup scheduler should work with defaults
                setup_scheduler()
                
                # Verify job was added
                job = scheduler.get_job('background_fetch')
                assert job is not None
