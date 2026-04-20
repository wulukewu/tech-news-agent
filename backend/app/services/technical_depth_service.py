"""
Technical Depth Service

This service manages technical depth threshold settings for filtering notifications
based on the technical complexity of articles.
"""

import logging
from enum import Enum
from typing import Dict, List, Optional, Tuple
from uuid import UUID

from app.core.exceptions import SupabaseServiceError
from app.services.supabase_service import SupabaseService

logger = logging.getLogger(__name__)


class TechnicalDepthLevel(Enum):
    """Technical depth levels for content filtering."""

    BASIC = "basic"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"

    @classmethod
    def get_numeric_value(cls, level: str) -> int:
        """Get numeric value for comparison."""
        mapping = {
            cls.BASIC.value: 1,
            cls.INTERMEDIATE.value: 2,
            cls.ADVANCED.value: 3,
            cls.EXPERT.value: 4,
        }
        return mapping.get(level, 1)

    @classmethod
    def get_description(cls, level: str) -> str:
        """Get human-readable description of the level."""
        descriptions = {
            cls.BASIC.value: "基礎 - 適合初學者，包含基本概念和入門教學",
            cls.INTERMEDIATE.value: "中等 - 需要一定技術背景，包含實作細節",
            cls.ADVANCED.value: "進階 - 深入的技術討論，需要豐富經驗",
            cls.EXPERT.value: "專家 - 最深入的技術文章，適合專業人士",
        }
        return descriptions.get(level, "未知深度等級")

    @classmethod
    def get_all_levels(cls) -> List[Dict[str, str]]:
        """Get all levels with descriptions."""
        return [
            {
                "value": level.value,
                "label": level.value.title(),
                "description": cls.get_description(level.value),
                "numeric_value": cls.get_numeric_value(level.value),
            }
            for level in cls
        ]


class TechnicalDepthSettings:
    """Data class for technical depth settings."""

    def __init__(
        self, user_id: UUID, threshold: str = TechnicalDepthLevel.BASIC.value, enabled: bool = False
    ):
        self.user_id = user_id
        self.threshold = threshold
        self.enabled = enabled

    def to_dict(self) -> Dict:
        """Convert to dictionary for API responses."""
        return {
            "user_id": str(self.user_id),
            "threshold": self.threshold,
            "enabled": self.enabled,
            "threshold_description": TechnicalDepthLevel.get_description(self.threshold),
            "threshold_numeric": TechnicalDepthLevel.get_numeric_value(self.threshold),
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "TechnicalDepthSettings":
        """Create from dictionary."""
        return cls(
            user_id=UUID(data["user_id"]),
            threshold=data.get("threshold", TechnicalDepthLevel.BASIC.value),
            enabled=data.get("enabled", False),
        )


class TechnicalDepthService:
    """Service for managing technical depth threshold settings."""

    def __init__(self, supabase_service: Optional[SupabaseService] = None):
        self.supabase_service = supabase_service or SupabaseService()

    async def get_tech_depth_settings(self, user_id: UUID) -> TechnicalDepthSettings:
        """
        Get technical depth settings for a user.

        Args:
            user_id: The user's UUID

        Returns:
            TechnicalDepthSettings object
        """
        try:
            logger.info(f"Fetching technical depth settings for user {user_id}")

            result = (
                self.supabase_service.client.table("user_notification_preferences")
                .select("tech_depth_threshold, tech_depth_enabled")
                .eq("user_id", str(user_id))
                .execute()
            )

            if not result.data:
                logger.info(
                    f"No notification preferences found for user {user_id}, creating defaults"
                )
                # Create default preferences if they don't exist
                await self._create_default_preferences(user_id)
                return TechnicalDepthSettings(user_id=user_id)

            data = result.data[0]
            settings = TechnicalDepthSettings(
                user_id=user_id,
                threshold=data.get("tech_depth_threshold", TechnicalDepthLevel.BASIC.value),
                enabled=data.get("tech_depth_enabled", False),
            )

            logger.info(
                f"Retrieved technical depth settings for user {user_id}: {settings.threshold} (enabled: {settings.enabled})"
            )
            return settings

        except Exception as e:
            logger.error(f"Failed to get technical depth settings for user {user_id}: {e}")
            raise SupabaseServiceError(f"Failed to get technical depth settings: {e}")

    async def update_tech_depth_settings(
        self, user_id: UUID, threshold: Optional[str] = None, enabled: Optional[bool] = None
    ) -> TechnicalDepthSettings:
        """
        Update technical depth settings for a user.

        Args:
            user_id: The user's UUID
            threshold: Technical depth threshold level
            enabled: Whether technical depth filtering is enabled

        Returns:
            Updated TechnicalDepthSettings object
        """
        try:
            logger.info(f"Updating technical depth settings for user {user_id}")

            # Validate threshold if provided
            if threshold is not None:
                self._validate_threshold(threshold)

            # Prepare update data
            update_data = {}
            if threshold is not None:
                update_data["tech_depth_threshold"] = threshold
            if enabled is not None:
                update_data["tech_depth_enabled"] = enabled

            if not update_data:
                # No updates provided, return current settings
                return await self.get_tech_depth_settings(user_id)

            # Update the record
            result = (
                self.supabase_service.client.table("user_notification_preferences")
                .update(update_data)
                .eq("user_id", str(user_id))
                .execute()
            )

            if not result.data:
                # Record might not exist, try to create it
                logger.info(f"No existing preferences for user {user_id}, creating new record")
                await self._create_default_preferences(user_id)

                # Try update again
                result = (
                    self.supabase_service.client.table("user_notification_preferences")
                    .update(update_data)
                    .eq("user_id", str(user_id))
                    .execute()
                )

                if not result.data:
                    raise SupabaseServiceError("Failed to update technical depth settings")

            # Return updated settings
            updated_settings = await self.get_tech_depth_settings(user_id)
            logger.info(f"Updated technical depth settings for user {user_id}")

            return updated_settings

        except Exception as e:
            logger.error(f"Failed to update technical depth settings for user {user_id}: {e}")
            raise SupabaseServiceError(f"Failed to update technical depth settings: {e}")

    async def should_send_notification(
        self, user_id: UUID, article_tech_depth: Optional[str] = None
    ) -> Tuple[bool, str]:
        """
        Check if a notification should be sent based on technical depth filtering.

        Args:
            user_id: The user's UUID
            article_tech_depth: Technical depth level of the article

        Returns:
            Tuple of (should_send, reason)
        """
        try:
            settings = await self.get_tech_depth_settings(user_id)

            # If filtering is disabled, always send
            if not settings.enabled:
                return True, "Technical depth filtering is disabled"

            # If article has no depth rating, use basic level
            if not article_tech_depth:
                article_tech_depth = TechnicalDepthLevel.BASIC.value

            # Compare depth levels
            user_threshold = TechnicalDepthLevel.get_numeric_value(settings.threshold)
            article_depth = TechnicalDepthLevel.get_numeric_value(article_tech_depth)

            should_send = article_depth >= user_threshold

            if should_send:
                reason = f"Article depth ({article_tech_depth}) meets user threshold ({settings.threshold})"
            else:
                reason = f"Article depth ({article_tech_depth}) below user threshold ({settings.threshold})"

            logger.debug(f"Technical depth check for user {user_id}: {reason}")

            return should_send, reason

        except Exception as e:
            logger.error(f"Failed to check technical depth for user {user_id}: {e}")
            # Return True on error to avoid blocking notifications
            return True, f"Error checking technical depth: {e}"

    async def get_filtering_stats(self, user_id: UUID) -> Dict:
        """
        Get statistics about how technical depth filtering affects notifications.

        Args:
            user_id: The user's UUID

        Returns:
            Dictionary with filtering statistics
        """
        try:
            settings = await self.get_tech_depth_settings(user_id)

            if not settings.enabled:
                return {
                    "enabled": False,
                    "threshold": settings.threshold,
                    "message": "技術深度篩選已停用，將接收所有文章通知",
                }

            # Get article counts by depth level (this would need to be implemented based on your article schema)
            # For now, return basic stats
            threshold_numeric = TechnicalDepthLevel.get_numeric_value(settings.threshold)

            stats = {
                "enabled": True,
                "threshold": settings.threshold,
                "threshold_description": TechnicalDepthLevel.get_description(settings.threshold),
                "threshold_numeric": threshold_numeric,
                "message": f"只會接收 {settings.threshold} 等級以上的文章通知",
            }

            return stats

        except Exception as e:
            logger.error(f"Failed to get filtering stats for user {user_id}: {e}")
            return {"enabled": False, "error": str(e), "message": "無法載入篩選統計資料"}

    def _validate_threshold(self, threshold: str) -> None:
        """Validate technical depth threshold."""
        valid_levels = [level.value for level in TechnicalDepthLevel]
        if threshold not in valid_levels:
            raise ValueError(
                f"Invalid technical depth threshold: {threshold}. Must be one of: {valid_levels}"
            )

    async def _create_default_preferences(self, user_id: UUID) -> None:
        """Create default notification preferences for a user."""
        try:
            default_data = {
                "user_id": str(user_id),
                "frequency": "weekly",
                "notification_time": "18:00:00",
                "timezone": "UTC",
                "dm_enabled": True,
                "email_enabled": False,
                "tech_depth_threshold": TechnicalDepthLevel.BASIC.value,
                "tech_depth_enabled": False,
            }

            result = (
                self.supabase_service.client.table("user_notification_preferences")
                .insert(default_data)
                .execute()
            )

            if not result.data:
                raise SupabaseServiceError("Failed to create default preferences")

            logger.info(f"Created default notification preferences for user {user_id}")

        except Exception as e:
            logger.error(f"Failed to create default preferences for user {user_id}: {e}")
            raise SupabaseServiceError(f"Failed to create default preferences: {e}")

    @staticmethod
    def get_available_levels() -> List[Dict[str, str]]:
        """Get all available technical depth levels."""
        return TechnicalDepthLevel.get_all_levels()

    @staticmethod
    def estimate_article_depth(content: str, title: str = "") -> str:
        """
        Estimate the technical depth of an article based on its content.
        This is a simple heuristic-based approach.

        Args:
            content: Article content
            title: Article title

        Returns:
            Estimated technical depth level
        """
        # Simple keyword-based heuristic
        text = (title + " " + content).lower()

        # Expert level indicators
        expert_keywords = [
            "algorithm",
            "complexity",
            "optimization",
            "performance",
            "scalability",
            "architecture",
            "design pattern",
            "microservices",
            "distributed",
            "concurrency",
            "threading",
            "async",
            "memory management",
            "garbage collection",
            "compiler",
            "interpreter",
            "virtual machine",
            "bytecode",
            "assembly",
        ]

        # Advanced level indicators
        advanced_keywords = [
            "framework",
            "library",
            "api",
            "database",
            "sql",
            "nosql",
            "testing",
            "debugging",
            "profiling",
            "deployment",
            "devops",
            "security",
            "authentication",
            "authorization",
            "encryption",
            "networking",
            "protocol",
            "http",
            "tcp",
            "websocket",
        ]

        # Intermediate level indicators
        intermediate_keywords = [
            "function",
            "class",
            "object",
            "method",
            "variable",
            "loop",
            "condition",
            "array",
            "list",
            "dictionary",
            "exception",
            "error",
            "debug",
            "git",
            "version control",
        ]

        # Count keyword matches
        expert_count = sum(1 for keyword in expert_keywords if keyword in text)
        advanced_count = sum(1 for keyword in advanced_keywords if keyword in text)
        intermediate_count = sum(1 for keyword in intermediate_keywords if keyword in text)

        # Determine level based on keyword density
        total_words = len(text.split())
        if total_words == 0:
            return TechnicalDepthLevel.BASIC.value

        expert_ratio = expert_count / total_words
        advanced_ratio = advanced_count / total_words
        intermediate_ratio = intermediate_count / total_words

        if expert_ratio > 0.02 or expert_count >= 3:
            return TechnicalDepthLevel.EXPERT.value
        elif advanced_ratio > 0.03 or advanced_count >= 5:
            return TechnicalDepthLevel.ADVANCED.value
        elif intermediate_ratio > 0.05 or intermediate_count >= 3:
            return TechnicalDepthLevel.INTERMEDIATE.value
        else:
            return TechnicalDepthLevel.BASIC.value
