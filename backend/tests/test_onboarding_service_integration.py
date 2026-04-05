"""
Integration tests for OnboardingService

These tests verify the OnboardingService works correctly with realistic
database interactions and edge cases.
"""

import pytest
from uuid import uuid4
from unittest.mock import Mock
from datetime import datetime, timezone

from app.services.onboarding_service import OnboardingService, OnboardingServiceError
from app.schemas.onboarding import OnboardingStatus


@pytest.fixture
def mock_supabase_client():
    """Create a mock Supabase client with realistic response structure"""
    client = Mock()
    return client


@pytest.fixture
def onboarding_service(mock_supabase_client):
    """Create an OnboardingService instance"""
    return OnboardingService(mock_supabase_client)


class TestOnboardingWorkflow:
    """Test complete onboarding workflow scenarios"""
    
    @pytest.mark.asyncio
    async def test_complete_onboarding_flow(self, onboarding_service, mock_supabase_client):
        """Test a user going through the complete onboarding flow"""
        user_id = uuid4()
        
        # Step 1: Get initial status (no preferences exist)
        mock_select_response = Mock()
        mock_select_response.data = []
        
        mock_insert_response = Mock()
        mock_insert_response.data = [{'user_id': str(user_id)}]
        
        mock_table = Mock()
        mock_table.select.return_value.eq.return_value.execute.return_value = mock_select_response
        mock_table.insert.return_value.execute.return_value = mock_insert_response
        mock_supabase_client.table.return_value = mock_table
        
        status = await onboarding_service.get_onboarding_status(user_id)
        assert status.onboarding_completed is False
        assert status.onboarding_step is None
        
        # Step 2: Update progress to 'welcome' step
        mock_select_response.data = [{
            'user_id': str(user_id),
            'onboarding_started_at': None
        }]
        mock_update_response = Mock()
        mock_update_response.data = [{'user_id': str(user_id)}]
        mock_table.update.return_value.eq.return_value.execute.return_value = mock_update_response
        
        await onboarding_service.update_onboarding_progress(user_id, 'welcome', True)
        
        # Step 3: Update progress to 'recommendations' step
        mock_select_response.data = [{
            'user_id': str(user_id),
            'onboarding_started_at': datetime.now(timezone.utc).isoformat()
        }]
        
        await onboarding_service.update_onboarding_progress(user_id, 'recommendations', True)
        
        # Step 4: Mark as completed
        await onboarding_service.mark_onboarding_completed(user_id)
        
        # Verify all methods were called
        assert mock_table.insert.call_count >= 1
        assert mock_table.update.call_count >= 3
    
    @pytest.mark.asyncio
    async def test_skip_onboarding_flow(self, onboarding_service, mock_supabase_client):
        """Test a user skipping the onboarding flow"""
        user_id = uuid4()
        
        # Setup mocks
        mock_select_response = Mock()
        mock_select_response.data = [{'user_id': str(user_id)}]
        
        mock_update_response = Mock()
        mock_update_response.data = [{'user_id': str(user_id)}]
        
        mock_table = Mock()
        mock_table.select.return_value.eq.return_value.execute.return_value = mock_select_response
        mock_table.update.return_value.eq.return_value.execute.return_value = mock_update_response
        mock_supabase_client.table.return_value = mock_table
        
        # User skips onboarding
        await onboarding_service.mark_onboarding_skipped(user_id)
        
        # Verify update was called
        mock_table.update.assert_called_once()
        update_call_args = mock_table.update.call_args[0][0]
        assert update_call_args['onboarding_skipped'] is True
    
    @pytest.mark.asyncio
    async def test_reset_and_restart_onboarding(self, onboarding_service, mock_supabase_client):
        """Test resetting onboarding after completion"""
        user_id = uuid4()
        
        # Setup mocks for completed onboarding
        mock_select_response = Mock()
        mock_select_response.data = [{
            'user_id': str(user_id),
            'onboarding_completed': True,
            'onboarding_step': 'complete'
        }]
        
        mock_update_response = Mock()
        mock_update_response.data = [{'user_id': str(user_id)}]
        
        mock_table = Mock()
        mock_table.select.return_value.eq.return_value.execute.return_value = mock_select_response
        mock_table.update.return_value.eq.return_value.execute.return_value = mock_update_response
        mock_supabase_client.table.return_value = mock_table
        
        # Reset onboarding
        await onboarding_service.reset_onboarding(user_id)
        
        # Verify reset data
        update_call_args = mock_table.update.call_args[0][0]
        assert update_call_args['onboarding_completed'] is False
        assert update_call_args['onboarding_step'] is None
        assert update_call_args['onboarding_skipped'] is False


class TestEdgeCases:
    """Test edge cases and error scenarios"""
    
    @pytest.mark.asyncio
    async def test_multiple_progress_updates_same_step(self, onboarding_service, mock_supabase_client):
        """Test updating progress multiple times for the same step"""
        user_id = uuid4()
        
        mock_select_response = Mock()
        mock_select_response.data = [{
            'user_id': str(user_id),
            'onboarding_started_at': datetime.now(timezone.utc).isoformat()
        }]
        
        mock_update_response = Mock()
        mock_update_response.data = [{'user_id': str(user_id)}]
        
        mock_table = Mock()
        mock_table.select.return_value.eq.return_value.execute.return_value = mock_select_response
        mock_table.update.return_value.eq.return_value.execute.return_value = mock_update_response
        mock_supabase_client.table.return_value = mock_table
        
        # Update same step multiple times
        await onboarding_service.update_onboarding_progress(user_id, 'welcome', True)
        await onboarding_service.update_onboarding_progress(user_id, 'welcome', True)
        
        # Should succeed without errors
        assert mock_table.update.call_count == 2
    
    @pytest.mark.asyncio
    async def test_mark_completed_without_progress(self, onboarding_service, mock_supabase_client):
        """Test marking as completed without going through steps"""
        user_id = uuid4()
        
        mock_select_response = Mock()
        mock_select_response.data = [{'user_id': str(user_id)}]
        
        mock_update_response = Mock()
        mock_update_response.data = [{'user_id': str(user_id)}]
        
        mock_table = Mock()
        mock_table.select.return_value.eq.return_value.execute.return_value = mock_select_response
        mock_table.update.return_value.eq.return_value.execute.return_value = mock_update_response
        mock_supabase_client.table.return_value = mock_table
        
        # Mark as completed directly
        await onboarding_service.mark_onboarding_completed(user_id)
        
        # Should succeed
        update_call_args = mock_table.update.call_args[0][0]
        assert update_call_args['onboarding_completed'] is True
    
    @pytest.mark.asyncio
    async def test_skip_after_partial_completion(self, onboarding_service, mock_supabase_client):
        """Test skipping after completing some steps"""
        user_id = uuid4()
        
        mock_select_response = Mock()
        mock_select_response.data = [{
            'user_id': str(user_id),
            'onboarding_step': 'welcome',
            'onboarding_started_at': datetime.now(timezone.utc).isoformat()
        }]
        
        mock_update_response = Mock()
        mock_update_response.data = [{'user_id': str(user_id)}]
        
        mock_table = Mock()
        mock_table.select.return_value.eq.return_value.execute.return_value = mock_select_response
        mock_table.update.return_value.eq.return_value.execute.return_value = mock_update_response
        mock_supabase_client.table.return_value = mock_table
        
        # Skip after starting
        await onboarding_service.mark_onboarding_skipped(user_id)
        
        # Should succeed
        update_call_args = mock_table.update.call_args[0][0]
        assert update_call_args['onboarding_skipped'] is True


class TestDataConsistency:
    """Test data consistency and validation"""
    
    @pytest.mark.asyncio
    async def test_get_status_with_missing_fields(self, onboarding_service, mock_supabase_client):
        """Test getting status when some fields are missing from database"""
        user_id = uuid4()
        
        # Mock response with minimal fields
        mock_response = Mock()
        mock_response.data = [{
            'user_id': str(user_id)
            # Missing other fields
        }]
        
        mock_table = Mock()
        mock_table.select.return_value.eq.return_value.execute.return_value = mock_response
        mock_supabase_client.table.return_value = mock_table
        
        # Should handle missing fields gracefully
        status = await onboarding_service.get_onboarding_status(user_id)
        assert isinstance(status, OnboardingStatus)
        assert status.onboarding_completed is False  # Default value
        assert status.onboarding_skipped is False  # Default value
    
    @pytest.mark.asyncio
    async def test_update_includes_updated_at_timestamp(self, onboarding_service, mock_supabase_client):
        """Test that all updates include updated_at timestamp"""
        user_id = uuid4()
        
        mock_select_response = Mock()
        mock_select_response.data = [{
            'user_id': str(user_id),
            'onboarding_started_at': datetime.now(timezone.utc).isoformat()
        }]
        
        mock_update_response = Mock()
        mock_update_response.data = [{'user_id': str(user_id)}]
        
        mock_table = Mock()
        mock_table.select.return_value.eq.return_value.execute.return_value = mock_select_response
        mock_table.update.return_value.eq.return_value.execute.return_value = mock_update_response
        mock_supabase_client.table.return_value = mock_table
        
        # Test various update methods
        await onboarding_service.update_onboarding_progress(user_id, 'welcome', True)
        update_call_args = mock_table.update.call_args[0][0]
        assert 'updated_at' in update_call_args
        
        await onboarding_service.mark_onboarding_completed(user_id)
        update_call_args = mock_table.update.call_args[0][0]
        assert 'updated_at' in update_call_args
        
        await onboarding_service.mark_onboarding_skipped(user_id)
        update_call_args = mock_table.update.call_args[0][0]
        assert 'updated_at' in update_call_args
        
        await onboarding_service.reset_onboarding(user_id)
        update_call_args = mock_table.update.call_args[0][0]
        assert 'updated_at' in update_call_args
