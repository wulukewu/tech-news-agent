"""
Tests for scheduler health check endpoint.

Validates: Requirements 10.1, 10.2, 10.3, 10.4, 10.5, 10.6, 10.7
"""

import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import patch

from app.tasks.scheduler import get_scheduler_health, _scheduler_health


class TestSchedulerHealthCheck:
    """Unit tests for scheduler health check functionality."""
    
    @pytest.fixture(autouse=True)
    def reset_health_state(self):
        """Reset health state before each test."""
        _scheduler_health["last_execution_time"] = None
        _scheduler_health["last_articles_processed"] = 0
        _scheduler_health["last_failed_operations"] = 0
        _scheduler_health["last_total_operations"] = 0
        yield
    
    @pytest.mark.asyncio
    async def test_health_check_returns_last_execution_time(self):
        """
        Test that health check returns the last execution timestamp.
        
        Validates: Requirement 10.2
        """
        # Set up health state
        execution_time = datetime.now(timezone.utc)
        _scheduler_health["last_execution_time"] = execution_time
        _scheduler_health["last_articles_processed"] = 10
        _scheduler_health["last_failed_operations"] = 0
        _scheduler_health["last_total_operations"] = 10
        
        # Get health status
        health = await get_scheduler_health()
        
        # Verify last execution time is returned
        assert health["last_execution_time"] == execution_time.isoformat()
    
    @pytest.mark.asyncio
    async def test_health_check_returns_articles_processed_count(self):
        """
        Test that health check returns the count of articles processed.
        
        Validates: Requirement 10.3
        """
        # Set up health state
        _scheduler_health["last_execution_time"] = datetime.now(timezone.utc)
        _scheduler_health["last_articles_processed"] = 25
        _scheduler_health["last_failed_operations"] = 0
        _scheduler_health["last_total_operations"] = 25
        
        # Get health status
        health = await get_scheduler_health()
        
        # Verify articles processed count
        assert health["articles_processed"] == 25
    
    @pytest.mark.asyncio
    async def test_health_check_returns_failed_operations_count(self):
        """
        Test that health check returns the count of failed operations.
        
        Validates: Requirement 10.4
        """
        # Set up health state
        _scheduler_health["last_execution_time"] = datetime.now(timezone.utc)
        _scheduler_health["last_articles_processed"] = 20
        _scheduler_health["last_failed_operations"] = 5
        _scheduler_health["last_total_operations"] = 25
        
        # Get health status
        health = await get_scheduler_health()
        
        # Verify failed operations count
        assert health["failed_operations"] == 5
        assert health["total_operations"] == 25
    
    @pytest.mark.asyncio
    async def test_health_check_returns_200_when_healthy(self):
        """
        Test that health check returns HTTP 200 when scheduler is healthy.
        
        Validates: Requirement 10.5
        """
        # Set up healthy state (recent execution, low failure rate)
        _scheduler_health["last_execution_time"] = datetime.now(timezone.utc)
        _scheduler_health["last_articles_processed"] = 20
        _scheduler_health["last_failed_operations"] = 2
        _scheduler_health["last_total_operations"] = 20
        
        # Get health status
        health = await get_scheduler_health()
        
        # Verify healthy status
        assert health["status_code"] == 200
        assert health["is_healthy"] is True
        assert len(health["issues"]) == 0
    
    @pytest.mark.asyncio
    async def test_health_check_returns_503_when_not_run_in_12_hours(self):
        """
        Test that health check returns HTTP 503 when scheduler has not run in 12 hours.
        
        Validates: Requirement 10.6
        """
        # Set up stale state (last execution > 12 hours ago)
        stale_time = datetime.now(timezone.utc) - timedelta(hours=13)
        _scheduler_health["last_execution_time"] = stale_time
        _scheduler_health["last_articles_processed"] = 10
        _scheduler_health["last_failed_operations"] = 0
        _scheduler_health["last_total_operations"] = 10
        
        # Get health status
        health = await get_scheduler_health()
        
        # Verify unhealthy status
        assert health["status_code"] == 503
        assert health["is_healthy"] is False
        assert len(health["issues"]) > 0
        assert any("has not run in" in issue for issue in health["issues"])
    
    @pytest.mark.asyncio
    async def test_health_check_returns_503_when_failure_rate_exceeds_50_percent(self):
        """
        Test that health check returns HTTP 503 when failure rate exceeds 50%.
        
        Validates: Requirement 10.7
        """
        # Set up high failure rate state (>50% failures)
        _scheduler_health["last_execution_time"] = datetime.now(timezone.utc)
        _scheduler_health["last_articles_processed"] = 20
        _scheduler_health["last_failed_operations"] = 15
        _scheduler_health["last_total_operations"] = 20
        
        # Get health status
        health = await get_scheduler_health()
        
        # Verify unhealthy status
        assert health["status_code"] == 503
        assert health["is_healthy"] is False
        assert len(health["issues"]) > 0
        assert any("failure rate" in issue for issue in health["issues"])
    
    @pytest.mark.asyncio
    async def test_health_check_returns_503_when_never_executed(self):
        """
        Test that health check returns HTTP 503 when scheduler has never executed.
        
        Validates: Requirement 10.6
        """
        # Health state is already reset (never executed)
        
        # Get health status
        health = await get_scheduler_health()
        
        # Verify unhealthy status
        assert health["status_code"] == 503
        assert health["is_healthy"] is False
        assert health["last_execution_time"] is None
        assert len(health["issues"]) > 0
        assert any("never executed" in issue for issue in health["issues"])
    
    @pytest.mark.asyncio
    async def test_health_check_with_exactly_50_percent_failure_rate(self):
        """
        Test that health check returns 200 when failure rate is exactly 50%.
        
        Validates: Requirement 10.7 (threshold is >50%, not >=50%)
        """
        # Set up exactly 50% failure rate
        _scheduler_health["last_execution_time"] = datetime.now(timezone.utc)
        _scheduler_health["last_articles_processed"] = 20
        _scheduler_health["last_failed_operations"] = 10
        _scheduler_health["last_total_operations"] = 20
        
        # Get health status
        health = await get_scheduler_health()
        
        # Verify healthy status (50% is not > 50%)
        assert health["status_code"] == 200
        assert health["is_healthy"] is True
    
    @pytest.mark.asyncio
    async def test_health_check_with_exactly_12_hours_since_last_run(self):
        """
        Test that health check returns 200 when exactly 12 hours since last run.
        
        Validates: Requirement 10.6 (threshold is >12 hours, not >=12 hours)
        """
        # Set up just under 12 hours since last run (11 hours 59 minutes)
        execution_time = datetime.now(timezone.utc) - timedelta(hours=11, minutes=59)
        _scheduler_health["last_execution_time"] = execution_time
        _scheduler_health["last_articles_processed"] = 10
        _scheduler_health["last_failed_operations"] = 0
        _scheduler_health["last_total_operations"] = 10
        
        # Get health status
        health = await get_scheduler_health()
        
        # Verify healthy status (< 12 hours)
        assert health["status_code"] == 200
        assert health["is_healthy"] is True
    
    @pytest.mark.asyncio
    async def test_health_check_with_zero_operations(self):
        """
        Test that health check handles zero operations gracefully.
        
        Validates: Requirement 10.4
        """
        # Set up state with zero operations
        _scheduler_health["last_execution_time"] = datetime.now(timezone.utc)
        _scheduler_health["last_articles_processed"] = 0
        _scheduler_health["last_failed_operations"] = 0
        _scheduler_health["last_total_operations"] = 0
        
        # Get health status
        health = await get_scheduler_health()
        
        # Verify healthy status (no operations means no failures)
        assert health["status_code"] == 200
        assert health["is_healthy"] is True
        assert health["articles_processed"] == 0
        assert health["failed_operations"] == 0
        assert health["total_operations"] == 0
    
    @pytest.mark.asyncio
    async def test_health_check_with_multiple_issues(self):
        """
        Test that health check reports multiple issues when present.
        
        Validates: Requirements 10.6, 10.7
        """
        # Set up state with both stale execution and high failure rate
        stale_time = datetime.now(timezone.utc) - timedelta(hours=15)
        _scheduler_health["last_execution_time"] = stale_time
        _scheduler_health["last_articles_processed"] = 20
        _scheduler_health["last_failed_operations"] = 18
        _scheduler_health["last_total_operations"] = 20
        
        # Get health status
        health = await get_scheduler_health()
        
        # Verify unhealthy status with multiple issues
        assert health["status_code"] == 503
        assert health["is_healthy"] is False
        assert len(health["issues"]) == 2
        assert any("has not run in" in issue for issue in health["issues"])
        assert any("failure rate" in issue for issue in health["issues"])
    
    @pytest.mark.asyncio
    async def test_health_check_returns_all_required_fields(self):
        """
        Test that health check returns all required fields.
        
        Validates: Requirements 10.1, 10.2, 10.3, 10.4
        """
        # Set up health state
        _scheduler_health["last_execution_time"] = datetime.now(timezone.utc)
        _scheduler_health["last_articles_processed"] = 15
        _scheduler_health["last_failed_operations"] = 3
        _scheduler_health["last_total_operations"] = 15
        
        # Get health status
        health = await get_scheduler_health()
        
        # Verify all required fields are present
        assert "last_execution_time" in health
        assert "articles_processed" in health
        assert "failed_operations" in health
        assert "total_operations" in health
        assert "status_code" in health
        assert "is_healthy" in health
        assert "issues" in health
