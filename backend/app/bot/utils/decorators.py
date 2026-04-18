"""Discord bot decorators for user registration and authentication."""

import logging
from functools import wraps
from uuid import UUID

import discord

from app.core.exceptions import SupabaseServiceError
from app.services.supabase_service import SupabaseService

logger = logging.getLogger(__name__)


async def ensure_user_registered(interaction: discord.Interaction) -> UUID:
    """
    Ensure user exists in database and return user UUID.

    This function is called before any Discord command execution to ensure
    the user is registered in the database. It implements the multi-tenant
    user registration middleware pattern.

    Args:
        interaction: Discord interaction object containing user information

    Returns:
        User UUID from database

    Raises:
        SupabaseServiceError: If user registration fails after all retry attempts

    Validates: Requirements 1.1, 1.2, 1.3, 1.4, 1.5
    """
    discord_id = str(interaction.user.id)
    logger.info(f"Ensuring user registration for discord_id: {discord_id}")

    try:
        supabase = SupabaseService()
        user_uuid = await supabase.get_or_create_user(discord_id)
        logger.info(f"User registered successfully with UUID: {user_uuid}")
        return user_uuid

    except SupabaseServiceError as e:
        # Log the detailed error for debugging
        logger.error(
            f"Failed to register user {discord_id}: {e}",
            exc_info=True,
            extra={
                "discord_id": discord_id,
                "discord_username": str(interaction.user),
                "error_context": e.context if hasattr(e, "context") else {},
            },
        )
        # Re-raise to allow caller to handle
        raise

    except Exception as e:
        # Catch any unexpected errors and wrap them
        logger.error(
            f"Unexpected error during user registration for {discord_id}: {e}", exc_info=True
        )
        raise SupabaseServiceError(
            "無法註冊使用者，請稍後再試。",
            original_error=e,
            context={"discord_id": discord_id, "operation": "ensure_user_registered"},
        )


def require_user_registration(func):
    """
    Decorator to ensure user is registered before command execution.
    Adds user_uuid to the function arguments.

    This decorator wraps Discord command handlers to automatically register
    users before command execution. It calls ensure_user_registered and
    passes the user_uuid to the decorated function.

    Args:
        func: The async function to decorate (command handler)

    Returns:
        Wrapped async function with user registration

    Raises:
        None - errors are caught and displayed to the user

    Validates: Requirements 1.1, 1.2, 1.3

    Example:
        @require_user_registration
        async def my_command(self, interaction: discord.Interaction, user_uuid: UUID):
            # user_uuid is automatically provided
            pass
    """

    @wraps(func)
    async def wrapper(self, interaction: discord.Interaction, *args, **kwargs):
        try:
            user_uuid = await ensure_user_registered(interaction)
            return await func(self, interaction, user_uuid, *args, **kwargs)
        except Exception as e:
            logger.error(f"User registration failed: {e}")
            await interaction.response.send_message(
                "❌ 無法註冊使用者，請稍後再試。", ephemeral=True
            )

    return wrapper
