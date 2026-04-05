"""
Unit tests for OnboardingService

Tests the core functionality of the OnboardingService class including:
- Getting onboarding status
- Updating onboarding progress
- Marking onboarding as completed
- Marking onboarding as skipped
- Resetting onboarding state
"""

import pytest
from uuid import uuid4
from unittest.mock import Mock, AsyncMock, MagicMock
from datetime import datetime, timezone

from app.services.onboarding_service import OnboardingService, OnboardingServiceError
from app.schemas.onboarding import OnboardingStatus


@pytest.fixture
def mock_supabase_client():
    """Create a mock Supabase client"""
    client = Mock()
    client.table = Mock()
    return client


@pytest.fixture
def onboarding_service(mock_supabase_client):
    """Create an OnboardingService instance with mock client"""
    return OnboardingService(mock_supabase_client)


class TestGetOnboardingStatus:
    """Tests for get_onboarding_status method"""
    
    @pytest.mark.asyncio
    async def test_get_status_existing_user(self, onboarding_service, mock_supabase_client):
        """Test getting status for user with existing preferences"""
        user_id = uuid4()
        
        # Mock database response
        mock_response = Mock()
        mock_response.data = [{
            'user_id': str(user_id),
            'onboarding_completed': False,
            'onboarding_step': 'welcome',
            'onboarding_skipped': False,
            'tooltip_tour_completed': False
        }]
        
        mock_table = Mock()
        mock_table.select.return_value.eq.return_value.execute.return_value = mock_response
        mock_supabase_client.table.return_value = mock_table
        
        # Execute
        status = await onboarding_service.get_onboarding_status(user_id)
        
        # Verify
        assert isinstance(status, OnboardingStatus)
        assert status.onboarding_completed is False
        assert status.onboarding_step == 'welcome'
        assert status.onboarding_skipped is False
        assert status.tooltip_tour_completed is False
    
    @pytest.mark.asyncio
    async def test_get_status_new_user_creates_default(self, onboarding_service, mock_supabase_client):
        """Test getting status for new user creates default preferences"""
        user_id = uuid4()
        
        # Mock empty response for select
        mock_select_response = Mock()
        mock_select_response.data = []
        
        # Mock successful insert response
        mock_insert_response = Mock()
        mock_insert_response.data = [{'user_id': str(user_id)}]
        
        mock_table = Mock()
        mock_table.select.return_value.eq.return_value.execute.return_value = mock_select_response
        mock_table.insert.return_value.execute.return_value = mock_insert_response
        mock_supabase_client.table.return_value = mock_table
        
        # Execute
        status = await onboarding_service.get_onboarding_status(user_id)
        
        # Verify default status returned
        assert isinstance(status, OnboardingStatus)
        assert status.onboarding_completed is False
        assert status.onboarding_step is None
        assert status.onboarding_skipped is False
        assert status.tooltip_tour_completed is False
        
        # Verify insert was called
        mock_table.insert.assert_called_once()


class TestUpdateOnboardingProgress:
    """Tests for update_onboarding_progress method"""
    
    @pytest.mark.asyncio
    async def test_update_progress_success(self, onboarding_service, mock_supabase_client):
        """Test successfully updating onboarding progress"""
        user_id = uuid4()
        step = 'recommendations'
        
        # Mock existing preferences
        mock_select_response = Mock()
        mock_select_response.data = [{
            'user_id': str(user_id),
            'onboarding_started_at': datetime.now(timezone.utc).isoformat()
        }]
        
        # Mock successful update
        mock_update_response = Mock()
        mock_update_response.data = [{'user_id': str(user_id)}]
        
        mock_table = Mock()
        mock_table.select.return_value.eq.return_value.execute.return_value = mock_select_response
        mock_table.update.return_value.eq.return_value.execute.return_value = mock_update_response
        mock_supabase_client.table.return_value = mock_table
        
        # Execute
        await onboarding_service.update_onboarding_progress(user_id, step, True)
        
        # Verify update was called
        mock_table.update.assert_called_once()
        update_call_args = mock_table.update.call_args[0][0]
        assert update_call_args['onboarding_step'] == step
    
    @pytest.mark.asyncio
    async def test_update_progress_sets_started_at_for_first_step(self, onboarding_service, mock_supabase_client):
        """Test that first step update sets onboarding_started_at"""
        user_id = uuid4()
        
        # Mock existing preferences without started_at
        mock_select_response = Mock()
        mock_select_response.data = [{
            'user_id': str(user_id),
            'onboarding_started_at': None
        }]
        
        # Mock successful update
        mock_update_response = Mock()
        mock_update_response.data = [{'user_id': str(user_id)}]
        
        mock_table = Mock()
        mock_table.select.return_value.eq.return_value.execute.return_value = mock_select_response
        mock_table.update.return_value.eq.return_value.execute.return_value = mock_update_response
        mock_supabase_client.table.return_value = mock_table
        
        # Execute
        await onboarding_service.update_onboarding_progress(user_id, 'welcome', True)
        
        # Verify started_at was set
        update_call_args = mock_table.update.call_args[0][0]
        assert 'onboarding_started_at' in update_call_args


class TestMarkOnboardingCompleted:
    """Tests for mark_onboarding_completed method"""
    
    @pytest.mark.asyncio
    async def test_mark_completed_success(self, onboarding_service, mock_supabase_client):
        """Test successfully marking onboarding as completed"""
        user_id = uuid4()
        
        # Mock existing preferences
        mock_select_response = Mock()
        mock_select_response.data = [{'user_id': str(user_id)}]
        
        # Mock successful update
        mock_update_response = Mock()
        mock_update_response.data = [{'user_id': str(user_id)}]
        
        mock_table = Mock()
        mock_table.select.return_value.eq.return_value.execute.return_value = mock_select_response
        mock_table.update.return_value.eq.return_value.execute.return_value = mock_update_response
        mock_supabase_client.table.return_value = mock_table
        
        # Execute
        await onboarding_service.mark_onboarding_completed(user_id)
        
        # Verify update was called with correct data
        mock_table.update.assert_called_once()
        update_call_args = mock_table.update.call_args[0][0]
        assert update_call_args['onboarding_completed'] is True
        assert update_call_args['onboarding_step'] == 'complete'
        assert 'onboarding_completed_at' in update_call_args


class TestMarkOnboardingSkipped:
    """Tests for mark_onboarding_skipped method"""
    
    @pytest.mark.asyncio
    async def test_mark_skipped_success(self, onboarding_service, mock_supabase_client):
        """Test successfully marking onboarding as skipped"""
        user_id = uuid4()
        
        # Mock existing preferences
        mock_select_response = Mock()
        mock_select_response.data = [{'user_id': str(user_id)}]
        
        # Mock successful update
        mock_update_response = Mock()
        mock_update_response.data = [{'user_id': str(user_id)}]
        
        mock_table = Mock()
        mock_table.select.return_value.eq.return_value.execute.return_value = mock_select_response
        mock_table.update.return_value.eq.return_value.execute.return_value = mock_update_response
        mock_supabase_client.table.return_value = mock_table
        
        # Execute
        await onboarding_service.mark_onboarding_skipped(user_id)
        
        # Verify update was called with correct data
        mock_table.update.assert_called_once()
        update_call_args = mock_table.update.call_args[0][0]
        assert update_call_args['onboarding_skipped'] is True


class TestResetOnboarding:
    """Tests for reset_onboarding method"""
    
    @pytest.mark.asyncio
    async def test_reset_onboarding_success(self, onboarding_service, mock_supabase_client):
        """Test successfully resetting onboarding state"""
        user_id = uuid4()
        
        # Mock existing preferences
        mock_select_response = Mock()
        mock_select_response.data = [{'user_id': str(user_id)}]
        
        # Mock successful update
        mock_update_response = Mock()
        mock_update_response.data = [{'user_id': str(user_id)}]
        
        mock_table = Mock()
        mock_table.select.return_value.eq.return_value.execute.return_value = mock_select_response
        mock_table.update.return_value.eq.return_value.execute.return_value = mock_update_response
        mock_supabase_client.table.return_value = mock_table
        
        # Execute
        await onboarding_service.reset_onboarding(user_id)
        
        # Verify update was called with reset data
        mock_table.update.assert_called_once()
        update_call_args = mock_table.update.call_args[0][0]
        assert update_call_args['onboarding_completed'] is False
        assert update_call_args['onboarding_step'] is None
        assert update_call_args['onboarding_skipped'] is False
        assert update_call_args['onboarding_started_at'] is None
        assert update_call_args['onboarding_completed_at'] is None


class TestErrorHandling:
    """Tests for error handling"""
    
    @pytest.mark.asyncio
    async def test_get_status_database_error(self, onboarding_service, mock_supabase_client):
        """Test error handling when database query fails"""
        user_id = uuid4()
        
        # Mock database error
        mock_table = Mock()
        mock_table.select.return_value.eq.return_value.execute.side_effect = Exception("Database error")
        mock_supabase_client.table.return_value = mock_table
        
        # Execute and verify exception
        with pytest.raises(OnboardingServiceError):
            await onboarding_service.get_onboarding_status(user_id)
    
    @pytest.mark.asyncio
    async def test_update_progress_database_error(self, onboarding_service, mock_supabase_client):
        """Test error handling when update fails"""
        user_id = uuid4()
        
        # Mock database error
        mock_table = Mock()
        mock_table.select.return_value.eq.return_value.execute.side_effect = Exception("Database error")
        mock_supabase_client.table.return_value = mock_table
        
        # Execute and verify exception
        with pytest.raises(OnboardingServiceError):
            await onboarding_service.update_onboarding_progress(user_id, 'welcome', True)
