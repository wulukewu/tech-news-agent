"""
Unit tests for AnalyticsService

Tests the core functionality of the AnalyticsService class including:
- Logging analytics events
- Calculating onboarding completion rates
- Calculating drop-off rates
- Calculating average time per step
- Error handling

Requirements: 14.1, 14.3, 14.4, 14.5, 14.6
"""

import pytest
from uuid import uuid4
from unittest.mock import Mock
from datetime import datetime, timezone, timedelta

from app.services.analytics_service import AnalyticsService, AnalyticsServiceError
from app.schemas.analytics import (
    OnboardingCompletionRateResponse,
    DropOffRatesResponse,
    AverageTimePerStepResponse
)


@pytest.fixture
def mock_supabase_client():
    """Create a mock Supabase client"""
    client = Mock()
    client.table = Mock()
    return client


@pytest.fixture
def analytics_service(mock_supabase_client):
    """Create an AnalyticsService instance with mock client"""
    return AnalyticsService(mock_supabase_client)


class TestLogEvent:
    """Tests for log_event method"""
    
    @pytest.mark.asyncio
    async def test_log_event_success(self, analytics_service, mock_supabase_client):
        """Test successfully logging an analytics event"""
        user_id = uuid4()
        event_type = 'onboarding_started'
        event_data = {'source': 'web'}
        
        # Mock successful insert
        mock_response = Mock()
        mock_response.data = [{'id': str(uuid4())}]
        
        mock_table = Mock()
        mock_table.insert.return_value.execute.return_value = mock_response
        mock_supabase_client.table.return_value = mock_table
        
        # Execute
        await analytics_service.log_event(user_id, event_type, event_data)
        
        # Verify insert was called
        mock_table.insert.assert_called_once()
        insert_call_args = mock_table.insert.call_args[0][0]
        assert insert_call_args['user_id'] == str(user_id)
        assert insert_call_args['event_type'] == event_type
        assert insert_call_args['event_data'] == event_data
    
    @pytest.mark.asyncio
    async def test_log_event_with_empty_data(self, analytics_service, mock_supabase_client):
        """Test logging event with no event_data"""
        user_id = uuid4()
        event_type = 'onboarding_started'
        
        # Mock successful insert
        mock_response = Mock()
        mock_response.data = [{'id': str(uuid4())}]
        
        mock_table = Mock()
        mock_table.insert.return_value.execute.return_value = mock_response
        mock_supabase_client.table.return_value = mock_table
        
        # Execute
        await analytics_service.log_event(user_id, event_type)
        
        # Verify empty dict was used
        insert_call_args = mock_table.insert.call_args[0][0]
        assert insert_call_args['event_data'] == {}
    
    @pytest.mark.asyncio
    async def test_log_event_all_supported_types(self, analytics_service, mock_supabase_client):
        """Test logging all supported event types"""
        user_id = uuid4()
        
        # Mock successful insert
        mock_response = Mock()
        mock_response.data = [{'id': str(uuid4())}]
        
        mock_table = Mock()
        mock_table.insert.return_value.execute.return_value = mock_response
        mock_supabase_client.table.return_value = mock_table
        
        # Test each supported event type
        for event_type in AnalyticsService.SUPPORTED_EVENT_TYPES:
            await analytics_service.log_event(user_id, event_type)
            
            # Verify correct event type was logged
            insert_call_args = mock_table.insert.call_args[0][0]
            assert insert_call_args['event_type'] == event_type
    
    @pytest.mark.asyncio
    async def test_log_event_step_completed_with_time(self, analytics_service, mock_supabase_client):
        """Test logging step_completed event with time_spent_seconds"""
        user_id = uuid4()
        event_type = 'step_completed'
        event_data = {
            'step': 'welcome',
            'time_spent_seconds': 45
        }
        
        # Mock successful insert
        mock_response = Mock()
        mock_response.data = [{'id': str(uuid4())}]
        
        mock_table = Mock()
        mock_table.insert.return_value.execute.return_value = mock_response
        mock_supabase_client.table.return_value = mock_table
        
        # Execute
        await analytics_service.log_event(user_id, event_type, event_data)
        
        # Verify event data includes time
        insert_call_args = mock_table.insert.call_args[0][0]
        assert insert_call_args['event_data']['time_spent_seconds'] == 45
    
    @pytest.mark.asyncio
    async def test_log_event_onboarding_skipped_with_step(self, analytics_service, mock_supabase_client):
        """Test logging onboarding_skipped event with step information"""
        user_id = uuid4()
        event_type = 'onboarding_skipped'
        event_data = {
            'step': 'recommendations',
            'reason': 'user_clicked_skip'
        }
        
        # Mock successful insert
        mock_response = Mock()
        mock_response.data = [{'id': str(uuid4())}]
        
        mock_table = Mock()
        mock_table.insert.return_value.execute.return_value = mock_response
        mock_supabase_client.table.return_value = mock_table
        
        # Execute
        await analytics_service.log_event(user_id, event_type, event_data)
        
        # Verify step information is included
        insert_call_args = mock_table.insert.call_args[0][0]
        assert insert_call_args['event_data']['step'] == 'recommendations'
    
    @pytest.mark.asyncio
    async def test_log_event_database_error(self, analytics_service, mock_supabase_client):
        """Test error handling when database insert fails"""
        user_id = uuid4()
        event_type = 'onboarding_started'
        
        # Mock database error
        mock_table = Mock()
        mock_table.insert.return_value.execute.side_effect = Exception("Database error")
        mock_supabase_client.table.return_value = mock_table
        
        # Execute and verify exception
        with pytest.raises(AnalyticsServiceError):
            await analytics_service.log_event(user_id, event_type)


class TestGetOnboardingCompletionRate:
    """Tests for get_onboarding_completion_rate method"""
    
    @pytest.mark.asyncio
    async def test_completion_rate_with_data(self, analytics_service, mock_supabase_client):
        """Test calculating completion rate with actual data"""
        start_date = datetime(2024, 1, 1, tzinfo=timezone.utc)
        end_date = datetime(2024, 1, 31, tzinfo=timezone.utc)
        
        # Mock 100 users started
        started_users = [{'user_id': str(uuid4())} for _ in range(100)]
        mock_started_response = Mock()
        mock_started_response.data = started_users
        
        # Mock 75 users completed
        completed_users = started_users[:75]
        mock_completed_response = Mock()
        mock_completed_response.data = completed_users
        
        # Mock 15 users skipped
        skipped_users = started_users[75:90]
        mock_skipped_response = Mock()
        mock_skipped_response.data = skipped_users
        
        # Setup mock table
        mock_table = Mock()
        mock_supabase_client.table.return_value = mock_table
        
        # Configure mock to return different responses based on event_type
        def mock_select(*args, **kwargs):
            mock_chain = Mock()
            mock_chain.eq = Mock(return_value=mock_chain)
            mock_chain.gte = Mock(return_value=mock_chain)
            mock_chain.lte = Mock(return_value=mock_chain)
            
            # Store the event_type from eq() call
            original_eq = mock_chain.eq
            
            def eq_with_tracking(field, value):
                if field == 'event_type':
                    mock_chain._event_type = value
                return original_eq(field, value)
            
            mock_chain.eq = eq_with_tracking
            
            def execute():
                event_type = getattr(mock_chain, '_event_type', None)
                if event_type == 'onboarding_started':
                    return mock_started_response
                elif event_type == 'onboarding_finished':
                    return mock_completed_response
                elif event_type == 'onboarding_skipped':
                    return mock_skipped_response
                return Mock(data=[])
            
            mock_chain.execute = execute
            return mock_chain
        
        mock_table.select = mock_select
        
        # Execute
        result = await analytics_service.get_onboarding_completion_rate(start_date, end_date)
        
        # Verify
        assert isinstance(result, OnboardingCompletionRateResponse)
        assert result.total_users == 100
        assert result.completed_users == 75
        assert result.skipped_users == 15
        assert result.completion_rate == 75.0
    
    @pytest.mark.asyncio
    async def test_completion_rate_no_users(self, analytics_service, mock_supabase_client):
        """Test completion rate when no users started onboarding"""
        start_date = datetime(2024, 1, 1, tzinfo=timezone.utc)
        end_date = datetime(2024, 1, 31, tzinfo=timezone.utc)
        
        # Mock empty response
        mock_response = Mock()
        mock_response.data = []
        
        mock_table = Mock()
        mock_table.select.return_value.eq.return_value.gte.return_value.lte.return_value.execute.return_value = mock_response
        mock_supabase_client.table.return_value = mock_table
        
        # Execute
        result = await analytics_service.get_onboarding_completion_rate(start_date, end_date)
        
        # Verify
        assert result.total_users == 0
        assert result.completed_users == 0
        assert result.completion_rate == 0.0
    
    @pytest.mark.asyncio
    async def test_completion_rate_database_error(self, analytics_service, mock_supabase_client):
        """Test error handling when database query fails"""
        start_date = datetime(2024, 1, 1, tzinfo=timezone.utc)
        end_date = datetime(2024, 1, 31, tzinfo=timezone.utc)
        
        # Mock database error
        mock_table = Mock()
        mock_table.select.return_value.eq.return_value.gte.return_value.lte.return_value.execute.side_effect = Exception("Database error")
        mock_supabase_client.table.return_value = mock_table
        
        # Execute and verify exception
        with pytest.raises(AnalyticsServiceError):
            await analytics_service.get_onboarding_completion_rate(start_date, end_date)


class TestGetDropOffRates:
    """Tests for get_drop_off_rates method"""
    
    @pytest.mark.asyncio
    async def test_drop_off_rates_with_data(self, analytics_service, mock_supabase_client):
        """Test calculating drop-off rates with actual data"""
        # Mock 100 users started
        started_users = [str(uuid4()) for _ in range(100)]
        mock_started_response = Mock()
        mock_started_response.data = [{'user_id': uid} for uid in started_users]
        
        # Mock step completions
        # 90 completed welcome, 75 completed recommendations, 70 completed final
        step_events = []
        for i, uid in enumerate(started_users):
            if i < 90:
                step_events.append({
                    'user_id': uid,
                    'event_data': {'step': 'welcome'}
                })
            if i < 75:
                step_events.append({
                    'user_id': uid,
                    'event_data': {'step': 'recommendations'}
                })
            if i < 70:
                step_events.append({
                    'user_id': uid,
                    'event_data': {'step': 'complete'}
                })
        
        mock_step_response = Mock()
        mock_step_response.data = step_events
        
        # Setup mock table
        mock_table = Mock()
        mock_supabase_client.table.return_value = mock_table
        
        def mock_select(*args, **kwargs):
            mock_chain = Mock()
            mock_chain.eq = Mock(return_value=mock_chain)
            
            # Store the event_type from eq() call
            original_eq = mock_chain.eq
            
            def eq_with_tracking(field, value):
                if field == 'event_type':
                    mock_chain._event_type = value
                return original_eq(field, value)
            
            mock_chain.eq = eq_with_tracking
            
            def execute():
                event_type = getattr(mock_chain, '_event_type', None)
                if event_type == 'step_completed':
                    return mock_step_response
                elif event_type == 'onboarding_started':
                    return mock_started_response
                return Mock(data=[])
            
            mock_chain.execute = execute
            return mock_chain
        
        mock_table.select = mock_select
        
        # Execute
        result = await analytics_service.get_drop_off_rates()
        
        # Verify
        assert isinstance(result, DropOffRatesResponse)
        assert result.total_started == 100
        assert 'welcome' in result.drop_off_by_step
        assert 'recommendations' in result.drop_off_by_step
        assert 'complete' in result.drop_off_by_step
        # Drop-off rate for welcome: (100 - 90) / 100 * 100 = 10%
        assert result.drop_off_by_step['welcome'] == 10.0
        # Drop-off rate for recommendations: (100 - 75) / 100 * 100 = 25%
        assert result.drop_off_by_step['recommendations'] == 25.0
    
    @pytest.mark.asyncio
    async def test_drop_off_rates_no_data(self, analytics_service, mock_supabase_client):
        """Test drop-off rates when no data exists"""
        # Mock empty response
        mock_response = Mock()
        mock_response.data = []
        
        mock_table = Mock()
        mock_table.select.return_value.eq.return_value.execute.return_value = mock_response
        mock_supabase_client.table.return_value = mock_table
        
        # Execute
        result = await analytics_service.get_drop_off_rates()
        
        # Verify
        assert result.total_started == 0
        assert result.drop_off_by_step == {}
    
    @pytest.mark.asyncio
    async def test_drop_off_rates_database_error(self, analytics_service, mock_supabase_client):
        """Test error handling when database query fails"""
        # Mock database error
        mock_table = Mock()
        mock_table.select.return_value.eq.return_value.execute.side_effect = Exception("Database error")
        mock_supabase_client.table.return_value = mock_table
        
        # Execute and verify exception
        with pytest.raises(AnalyticsServiceError):
            await analytics_service.get_drop_off_rates()


class TestGetAverageTimePerStep:
    """Tests for get_average_time_per_step method"""
    
    @pytest.mark.asyncio
    async def test_average_time_with_data(self, analytics_service, mock_supabase_client):
        """Test calculating average time per step with actual data"""
        # Mock step completion events with time data
        step_events = [
            {'event_data': {'step': 'welcome', 'time_spent_seconds': 30}},
            {'event_data': {'step': 'welcome', 'time_spent_seconds': 60}},
            {'event_data': {'step': 'welcome', 'time_spent_seconds': 45}},
            {'event_data': {'step': 'recommendations', 'time_spent_seconds': 120}},
            {'event_data': {'step': 'recommendations', 'time_spent_seconds': 180}},
            {'event_data': {'step': 'complete', 'time_spent_seconds': 20}},
            {'event_data': {'step': 'complete', 'time_spent_seconds': 40}},
        ]
        
        mock_response = Mock()
        mock_response.data = step_events
        
        mock_table = Mock()
        mock_table.select.return_value.eq.return_value.execute.return_value = mock_response
        mock_supabase_client.table.return_value = mock_table
        
        # Execute
        result = await analytics_service.get_average_time_per_step()
        
        # Verify
        assert isinstance(result, AverageTimePerStepResponse)
        assert result.total_completions == 7
        assert 'welcome' in result.average_time_by_step
        assert 'recommendations' in result.average_time_by_step
        assert 'complete' in result.average_time_by_step
        # Average for welcome: (30 + 60 + 45) / 3 = 45
        assert result.average_time_by_step['welcome'] == 45.0
        # Average for recommendations: (120 + 180) / 2 = 150
        assert result.average_time_by_step['recommendations'] == 150.0
        # Average for complete: (20 + 40) / 2 = 30
        assert result.average_time_by_step['complete'] == 30.0
    
    @pytest.mark.asyncio
    async def test_average_time_no_data(self, analytics_service, mock_supabase_client):
        """Test average time when no data exists"""
        # Mock empty response
        mock_response = Mock()
        mock_response.data = []
        
        mock_table = Mock()
        mock_table.select.return_value.eq.return_value.execute.return_value = mock_response
        mock_supabase_client.table.return_value = mock_table
        
        # Execute
        result = await analytics_service.get_average_time_per_step()
        
        # Verify
        assert result.total_completions == 0
        assert result.average_time_by_step == {}
    
    @pytest.mark.asyncio
    async def test_average_time_missing_time_data(self, analytics_service, mock_supabase_client):
        """Test average time when some events lack time_spent_seconds"""
        # Mock events with missing time data
        step_events = [
            {'event_data': {'step': 'welcome', 'time_spent_seconds': 30}},
            {'event_data': {'step': 'welcome'}},  # Missing time
            {'event_data': {'step': 'recommendations', 'time_spent_seconds': 120}},
        ]
        
        mock_response = Mock()
        mock_response.data = step_events
        
        mock_table = Mock()
        mock_table.select.return_value.eq.return_value.execute.return_value = mock_response
        mock_supabase_client.table.return_value = mock_table
        
        # Execute
        result = await analytics_service.get_average_time_per_step()
        
        # Verify - only events with time data are counted
        assert result.total_completions == 2
        assert result.average_time_by_step['welcome'] == 30.0
        assert result.average_time_by_step['recommendations'] == 120.0
    
    @pytest.mark.asyncio
    async def test_average_time_database_error(self, analytics_service, mock_supabase_client):
        """Test error handling when database query fails"""
        # Mock database error
        mock_table = Mock()
        mock_table.select.return_value.eq.return_value.execute.side_effect = Exception("Database error")
        mock_supabase_client.table.return_value = mock_table
        
        # Execute and verify exception
        with pytest.raises(AnalyticsServiceError):
            await analytics_service.get_average_time_per_step()


class TestEdgeCases:
    """Tests for edge cases and boundary conditions"""
    
    @pytest.mark.asyncio
    async def test_log_event_with_complex_event_data(self, analytics_service, mock_supabase_client):
        """Test logging event with complex nested event_data"""
        user_id = uuid4()
        event_type = 'feed_subscribed_from_onboarding'
        event_data = {
            'feed_id': str(uuid4()),
            'feed_name': 'Hacker News',
            'category': 'Tech News',
            'metadata': {
                'source': 'onboarding_modal',
                'position': 1,
                'recommended': True
            }
        }
        
        # Mock successful insert
        mock_response = Mock()
        mock_response.data = [{'id': str(uuid4())}]
        
        mock_table = Mock()
        mock_table.insert.return_value.execute.return_value = mock_response
        mock_supabase_client.table.return_value = mock_table
        
        # Execute
        await analytics_service.log_event(user_id, event_type, event_data)
        
        # Verify complex data is preserved
        insert_call_args = mock_table.insert.call_args[0][0]
        assert insert_call_args['event_data']['metadata']['recommended'] is True
    
    @pytest.mark.asyncio
    async def test_completion_rate_all_users_completed(self, analytics_service, mock_supabase_client):
        """Test completion rate when all users completed onboarding"""
        start_date = datetime(2024, 1, 1, tzinfo=timezone.utc)
        end_date = datetime(2024, 1, 31, tzinfo=timezone.utc)
        
        # Mock 50 users started and all completed
        users = [{'user_id': str(uuid4())} for _ in range(50)]
        mock_started_response = Mock()
        mock_started_response.data = users
        
        mock_completed_response = Mock()
        mock_completed_response.data = users
        
        mock_skipped_response = Mock()
        mock_skipped_response.data = []
        
        # Setup mock table
        mock_table = Mock()
        mock_supabase_client.table.return_value = mock_table
        
        def mock_select(*args, **kwargs):
            mock_chain = Mock()
            mock_chain.eq = Mock(return_value=mock_chain)
            mock_chain.gte = Mock(return_value=mock_chain)
            mock_chain.lte = Mock(return_value=mock_chain)
            
            original_eq = mock_chain.eq
            
            def eq_with_tracking(field, value):
                if field == 'event_type':
                    mock_chain._event_type = value
                return original_eq(field, value)
            
            mock_chain.eq = eq_with_tracking
            
            def execute():
                event_type = getattr(mock_chain, '_event_type', None)
                if event_type == 'onboarding_started':
                    return mock_started_response
                elif event_type == 'onboarding_finished':
                    return mock_completed_response
                elif event_type == 'onboarding_skipped':
                    return mock_skipped_response
                return Mock(data=[])
            
            mock_chain.execute = execute
            return mock_chain
        
        mock_table.select = mock_select
        
        # Execute
        result = await analytics_service.get_onboarding_completion_rate(start_date, end_date)
        
        # Verify 100% completion rate
        assert result.completion_rate == 100.0
        assert result.total_users == 50
        assert result.completed_users == 50
