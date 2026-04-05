"""
Onboarding Service

This module provides the OnboardingService class for managing user onboarding
progress, including tracking steps, completion status, and skip functionality.

Requirements: 1.4, 1.5, 1.6, 10.3, 10.6
"""

import logging
from uuid import UUID
from typing import Optional
from datetime import datetime, timezone

from supabase import Client

from app.schemas.onboarding import OnboardingStatus, UserPreferences


logger = logging.getLogger(__name__)


class OnboardingServiceError(Exception):
    """Base exception for OnboardingService errors"""
    pass


class OnboardingService:
    """
    Service for managing user onboarding progress and state.
    
    This service handles:
    - Retrieving onboarding status
    - Updating onboarding progress
    - Marking onboarding as completed or skipped
    - Resetting onboarding state
    
    Requirements: 1.4, 1.5, 1.6, 10.3, 10.6
    """
    
    def __init__(self, supabase_client: Client):
        """
        Initialize the OnboardingService.
        
        Args:
            supabase_client: Supabase client instance for database operations
        """
        self.client = supabase_client
        self.logger = logging.getLogger(__name__)
    
    async def get_onboarding_status(self, user_id: UUID) -> OnboardingStatus:
        """
        Get the current onboarding status for a user.
        
        If the user doesn't have a preferences record, creates one with default values.
        
        Args:
            user_id: UUID of the user
            
        Returns:
            OnboardingStatus with current progress and state
            
        Raises:
            OnboardingServiceError: If database operation fails
            
        Requirements: 1.4, 10.3, 10.4
        """
        try:
            self.logger.info(f"Getting onboarding status for user {user_id}")
            
            # Query user_preferences table
            response = self.client.table('user_preferences') \
                .select('*') \
                .eq('user_id', str(user_id)) \
                .execute()
            
            # If no preferences exist, create default record
            if not response.data:
                self.logger.info(f"No preferences found for user {user_id}, creating default record")
                await self._create_default_preferences(user_id)
                
                # Return default status
                return OnboardingStatus(
                    onboarding_completed=False,
                    onboarding_step=None,
                    onboarding_skipped=False,
                    tooltip_tour_completed=False,
                    should_show_onboarding=True  # New users should see onboarding
                )
            
            # Extract preferences data
            prefs = response.data[0]
            
            # Compute should_show_onboarding based on completion and skip states
            # Requirements 10.4, 10.5: Show onboarding only if NOT completed AND NOT skipped
            should_show = not prefs.get('onboarding_completed', False) and not prefs.get('onboarding_skipped', False)
            
            return OnboardingStatus(
                onboarding_completed=prefs.get('onboarding_completed', False),
                onboarding_step=prefs.get('onboarding_step'),
                onboarding_skipped=prefs.get('onboarding_skipped', False),
                tooltip_tour_completed=prefs.get('tooltip_tour_completed', False),
                should_show_onboarding=should_show
            )
            
        except Exception as e:
            self.logger.error(f"Failed to get onboarding status for user {user_id}: {e}")
            raise OnboardingServiceError(f"Failed to get onboarding status: {str(e)}")
    
    async def update_onboarding_progress(
        self,
        user_id: UUID,
        step: str,
        completed: bool
    ) -> None:
        """
        Update the user's onboarding progress.
        
        Sets the current onboarding step and optionally marks it as completed.
        If this is the first step, sets onboarding_started_at timestamp.
        
        Args:
            user_id: UUID of the user
            step: Current onboarding step (e.g., 'welcome', 'recommendations', 'complete')
            completed: Whether the step is completed
            
        Raises:
            OnboardingServiceError: If database operation fails
            
        Requirements: 1.4, 10.3
        """
        try:
            self.logger.info(f"Updating onboarding progress for user {user_id}: step={step}, completed={completed}")
            
            # Ensure preferences record exists
            await self._ensure_preferences_exist(user_id)
            
            # Prepare update data
            update_data = {
                'onboarding_step': step,
                'updated_at': datetime.now(timezone.utc).isoformat()
            }
            
            # If this is the first step, set started_at timestamp
            current_prefs = await self._get_preferences(user_id)
            if current_prefs and not current_prefs.get('onboarding_started_at'):
                update_data['onboarding_started_at'] = datetime.now(timezone.utc).isoformat()
            
            # Update the record
            response = self.client.table('user_preferences') \
                .update(update_data) \
                .eq('user_id', str(user_id)) \
                .execute()
            
            if not response.data:
                raise OnboardingServiceError(f"Failed to update onboarding progress for user {user_id}")
            
            self.logger.info(f"Successfully updated onboarding progress for user {user_id}")
            
        except OnboardingServiceError:
            raise
        except Exception as e:
            self.logger.error(f"Failed to update onboarding progress for user {user_id}: {e}")
            raise OnboardingServiceError(f"Failed to update onboarding progress: {str(e)}")
    
    async def mark_onboarding_completed(self, user_id: UUID) -> None:
        """
        Mark the user's onboarding as completed.
        
        Sets onboarding_completed to True and records the completion timestamp.
        
        Args:
            user_id: UUID of the user
            
        Raises:
            OnboardingServiceError: If database operation fails
            
        Requirements: 1.5, 10.3
        """
        try:
            self.logger.info(f"Marking onboarding as completed for user {user_id}")
            
            # Ensure preferences record exists
            await self._ensure_preferences_exist(user_id)
            
            # Update the record
            update_data = {
                'onboarding_completed': True,
                'onboarding_completed_at': datetime.now(timezone.utc).isoformat(),
                'onboarding_step': 'complete',
                'updated_at': datetime.now(timezone.utc).isoformat()
            }
            
            response = self.client.table('user_preferences') \
                .update(update_data) \
                .eq('user_id', str(user_id)) \
                .execute()
            
            if not response.data:
                raise OnboardingServiceError(f"Failed to mark onboarding as completed for user {user_id}")
            
            self.logger.info(f"Successfully marked onboarding as completed for user {user_id}")
            
        except OnboardingServiceError:
            raise
        except Exception as e:
            self.logger.error(f"Failed to mark onboarding as completed for user {user_id}: {e}")
            raise OnboardingServiceError(f"Failed to mark onboarding as completed: {str(e)}")
    
    async def mark_onboarding_skipped(self, user_id: UUID) -> None:
        """
        Mark the user's onboarding as skipped.
        
        Sets onboarding_skipped to True so the onboarding modal won't be shown again.
        
        Args:
            user_id: UUID of the user
            
        Raises:
            OnboardingServiceError: If database operation fails
            
        Requirements: 1.6, 1.7, 10.3
        """
        try:
            self.logger.info(f"Marking onboarding as skipped for user {user_id}")
            
            # Ensure preferences record exists
            await self._ensure_preferences_exist(user_id)
            
            # Update the record
            update_data = {
                'onboarding_skipped': True,
                'updated_at': datetime.now(timezone.utc).isoformat()
            }
            
            response = self.client.table('user_preferences') \
                .update(update_data) \
                .eq('user_id', str(user_id)) \
                .execute()
            
            if not response.data:
                raise OnboardingServiceError(f"Failed to mark onboarding as skipped for user {user_id}")
            
            self.logger.info(f"Successfully marked onboarding as skipped for user {user_id}")
            
        except OnboardingServiceError:
            raise
        except Exception as e:
            self.logger.error(f"Failed to mark onboarding as skipped for user {user_id}: {e}")
            raise OnboardingServiceError(f"Failed to mark onboarding as skipped: {str(e)}")
    
    async def reset_onboarding(self, user_id: UUID) -> None:
        """
        Reset the user's onboarding state.
        
        Clears all onboarding flags and timestamps, allowing the user to go through
        the onboarding flow again.
        
        Args:
            user_id: UUID of the user
            
        Raises:
            OnboardingServiceError: If database operation fails
            
        Requirements: 10.6, 10.7
        """
        try:
            self.logger.info(f"Resetting onboarding for user {user_id}")
            
            # Ensure preferences record exists
            await self._ensure_preferences_exist(user_id)
            
            # Reset all onboarding-related fields
            update_data = {
                'onboarding_completed': False,
                'onboarding_step': None,
                'onboarding_skipped': False,
                'onboarding_started_at': None,
                'onboarding_completed_at': None,
                'updated_at': datetime.now(timezone.utc).isoformat()
            }
            
            response = self.client.table('user_preferences') \
                .update(update_data) \
                .eq('user_id', str(user_id)) \
                .execute()
            
            if not response.data:
                raise OnboardingServiceError(f"Failed to reset onboarding for user {user_id}")
            
            self.logger.info(f"Successfully reset onboarding for user {user_id}")
            
        except OnboardingServiceError:
            raise
        except Exception as e:
            self.logger.error(f"Failed to reset onboarding for user {user_id}: {e}")
            raise OnboardingServiceError(f"Failed to reset onboarding: {str(e)}")
    
    # Private helper methods
    
    async def _get_preferences(self, user_id: UUID) -> Optional[dict]:
        """
        Get user preferences record.
        
        Args:
            user_id: UUID of the user
            
        Returns:
            Preferences dict or None if not found
        """
        response = self.client.table('user_preferences') \
            .select('*') \
            .eq('user_id', str(user_id)) \
            .execute()
        
        return response.data[0] if response.data else None
    
    async def _create_default_preferences(self, user_id: UUID) -> None:
        """
        Create a default preferences record for a user.
        
        Args:
            user_id: UUID of the user
            
        Raises:
            OnboardingServiceError: If creation fails
        """
        try:
            insert_data = {
                'user_id': str(user_id),
                'onboarding_completed': False,
                'onboarding_skipped': False,
                'tooltip_tour_completed': False,
                'tooltip_tour_skipped': False,
                'preferred_language': 'zh-TW'
            }
            
            response = self.client.table('user_preferences') \
                .insert(insert_data) \
                .execute()
            
            if not response.data:
                raise OnboardingServiceError(f"Failed to create default preferences for user {user_id}")
            
            self.logger.info(f"Created default preferences for user {user_id}")
            
        except Exception as e:
            self.logger.error(f"Failed to create default preferences for user {user_id}: {e}")
            raise OnboardingServiceError(f"Failed to create default preferences: {str(e)}")
    
    async def _ensure_preferences_exist(self, user_id: UUID) -> None:
        """
        Ensure a preferences record exists for the user, creating one if needed.
        
        Args:
            user_id: UUID of the user
        """
        prefs = await self._get_preferences(user_id)
        if not prefs:
            await self._create_default_preferences(user_id)
