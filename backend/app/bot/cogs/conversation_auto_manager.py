"""
Discord Bot Automatic Conversation Manager

Listens to Discord DM messages and automatically manages conversations:
- Detects when a user sends a DM and creates/resumes a conversation
- Tracks active sessions with a 30-minute inactivity timeout
- Saves each user message to the database with role="user", platform="discord"
- Notifies the user when a new conversation is created

Validates: Requirements 4.2
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional

import discord
from discord.ext import commands

from app.core.exceptions import SupabaseServiceError
from app.core.logger import get_logger
from app.repositories.conversation import ConversationRepository
from app.repositories.message import MessageRepository
from app.services.supabase_service import SupabaseService

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_SESSION_TIMEOUT_MINUTES: int = 30
_AUTO_TITLE_MAX_CHARS: int = 50
_AUTO_TITLE_MIN_CHARS: int = 5
_DEFAULT_TITLE: str = "Discord Conversation"


# ---------------------------------------------------------------------------
# Cog
# ---------------------------------------------------------------------------


class ConversationAutoManager(commands.Cog):
    """Cog that automatically manages conversations for Discord DM messages.

    Listens to every incoming message.  When the message arrives in a DM
    channel (not from a bot, not a slash command) the cog:

    1. Looks up the sender's active conversation from the in-memory cache.
    2. Creates a new conversation if none exists or the session has timed out.
    3. Saves the message to the database with ``role="user"`` and
       ``platform="discord"``.
    4. Sends a confirmation DM when a new conversation is created.

    All service dependencies are injected via ``__init__`` for testability.

    Validates: Requirements 4.2
    """

    def __init__(
        self,
        bot: commands.Bot,
        conversation_repo: Optional[ConversationRepository] = None,
        message_repo: Optional[MessageRepository] = None,
        supabase_service: Optional[SupabaseService] = None,
    ) -> None:
        """Initialise the cog with optional injected service dependencies.

        Args:
            bot: Discord bot instance.
            conversation_repo: Repository for conversation data access.
            message_repo: Repository for message data access.
            supabase_service: Supabase service used for user registration and
                client access.
        """
        self.bot = bot
        self._supabase_service = supabase_service or SupabaseService()

        client = self._supabase_service.client
        self.conversation_repo = conversation_repo or ConversationRepository(client)
        self.message_repo = message_repo or MessageRepository(client)

        # In-memory session state
        # discord_user_id (str) -> conversation_id (str)
        self._active_conversations: dict[str, str] = {}
        # discord_user_id (str) -> last message datetime (UTC-aware)
        self._last_activity: dict[str, datetime] = {}

        logger.info("ConversationAutoManager cog initialised")

    # ------------------------------------------------------------------
    # Event listener
    # ------------------------------------------------------------------

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        """Handle incoming Discord messages.

        Only processes DM messages that are not from bots and are not slash
        commands.  For each qualifying message the cog ensures an active
        conversation exists and persists the message to the database.

        Args:
            message: The incoming Discord message.
        """
        # Ignore messages from bots (including self)
        if message.author.bot:
            return

        # Only process DM channels
        if not isinstance(message.channel, discord.DMChannel):
            return

        # Skip slash commands (they start with '/')
        if message.content.startswith("/"):
            return

        discord_user_id = str(message.author.id)
        content = message.content

        logger.info(
            "Processing DM message",
            discord_user_id=discord_user_id,
            content_length=len(content),
        )

        try:
            # Resolve the system user UUID (creates the user if needed)
            system_user_id = await self._supabase_service.get_or_create_user(discord_user_id)

            # Get or create an active conversation
            conv_id, is_new = await self._get_or_create_conversation(
                discord_user_id=discord_user_id,
                system_user_id=str(system_user_id),
                first_message=content,
            )

            # Update last-activity timestamp
            self._last_activity[discord_user_id] = datetime.now(timezone.utc)

            # Persist the user message
            await self.message_repo.add_message(
                conversation_id=conv_id,
                role="user",
                content=content,
                platform="discord",
            )

            logger.info(
                "Message saved",
                discord_user_id=discord_user_id,
                conversation_id=conv_id,
                is_new_conversation=is_new,
            )

            # Notify the user when a brand-new conversation was created
            if is_new:
                notification = f"✅ 新對話已建立！ID: {conv_id[:8]}... " f"使用 /continue {conv_id} 繼續此對話"
                try:
                    await message.channel.send(notification)
                except discord.HTTPException as exc:
                    logger.warning(
                        "Failed to send new-conversation notification",
                        discord_user_id=discord_user_id,
                        error=str(exc),
                    )

        except SupabaseServiceError as exc:
            logger.error(
                "Database error while processing DM message",
                discord_user_id=discord_user_id,
                error=str(exc),
                exc_info=True,
            )
        except Exception as exc:
            logger.error(
                "Unexpected error while processing DM message",
                discord_user_id=discord_user_id,
                error=str(exc),
                error_type=type(exc).__name__,
                exc_info=True,
            )

    # ------------------------------------------------------------------
    # Helper methods
    # ------------------------------------------------------------------

    async def _get_or_create_conversation(
        self,
        discord_user_id: str,
        system_user_id: str,
        first_message: str,
    ) -> tuple[str, bool]:
        """Return the active conversation ID for the user, creating one if needed.

        A new conversation is created when:
        - The user has no active conversation in the cache, **or**
        - The last activity was more than ``_SESSION_TIMEOUT_MINUTES`` ago.

        Args:
            discord_user_id: Discord user ID string.
            system_user_id: System (database) user UUID string.
            first_message: Content of the first message (used for title
                generation when creating a new conversation).

        Returns:
            A tuple of ``(conversation_id, is_new)`` where ``is_new`` is
            ``True`` when a new conversation was created.

        Raises:
            SupabaseServiceError: If the database operation fails.
        """
        if self._is_session_active(discord_user_id):
            # Reuse the existing conversation
            conv_id = self._active_conversations[discord_user_id]
            logger.debug(
                "Reusing active conversation",
                discord_user_id=discord_user_id,
                conversation_id=conv_id,
            )
            return conv_id, False

        # Create a new conversation
        title = self._generate_title(first_message)
        conversation = await self.conversation_repo.create_conversation(
            user_id=system_user_id,
            title=title,
            platform="discord",
        )
        conv_id = str(conversation.id)

        # Update the in-memory cache
        self._active_conversations[discord_user_id] = conv_id
        self._last_activity[discord_user_id] = datetime.now(timezone.utc)

        logger.info(
            "New conversation created",
            discord_user_id=discord_user_id,
            conversation_id=conv_id,
            title=title,
        )
        return conv_id, True

    def _is_session_active(self, discord_user_id: str) -> bool:
        """Return ``True`` if the user has an active, non-timed-out session.

        A session is considered active when:
        - There is a cached conversation ID for the user, **and**
        - The last activity was within ``_SESSION_TIMEOUT_MINUTES`` minutes.

        Args:
            discord_user_id: Discord user ID string.

        Returns:
            ``True`` if the session is active, ``False`` otherwise.
        """
        if discord_user_id not in self._active_conversations:
            return False

        last_activity = self._last_activity.get(discord_user_id)
        if last_activity is None:
            return False

        elapsed = datetime.now(timezone.utc) - last_activity
        return elapsed < timedelta(minutes=_SESSION_TIMEOUT_MINUTES)

    def _generate_title(self, content: str) -> str:
        """Generate a conversation title from the first message content.

        Rules:
        - If the content is shorter than ``_AUTO_TITLE_MIN_CHARS`` characters,
          return ``_DEFAULT_TITLE``.
        - Otherwise return the first ``_AUTO_TITLE_MAX_CHARS`` characters of
          the content (stripped of leading/trailing whitespace).

        Args:
            content: The first message content.

        Returns:
            A title string.
        """
        stripped = content.strip()
        if len(stripped) < _AUTO_TITLE_MIN_CHARS:
            return _DEFAULT_TITLE
        return stripped[:_AUTO_TITLE_MAX_CHARS]


# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------


async def setup(bot: commands.Bot) -> None:
    """Load the ConversationAutoManager cog with injected service dependencies."""
    supabase_service = SupabaseService()
    client = supabase_service.client

    conversation_repo = ConversationRepository(client)
    message_repo = MessageRepository(client)

    await bot.add_cog(
        ConversationAutoManager(
            bot,
            conversation_repo=conversation_repo,
            message_repo=message_repo,
            supabase_service=supabase_service,
        )
    )
