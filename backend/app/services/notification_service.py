"""
Notification Service

This module provides the NotificationService class for orchestrating notification
delivery across multiple channels (Discord DM + Email). Integrates with existing
Discord bot for DM sending and implements email service with HTML and text formats.
Includes retry logic and error handling for failed deliveries.

Requirements: 9.1, 9.2, 9.3, 9.4, 9.5, 10.6
"""

import asyncio
import smtplib
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Dict, List, Optional
from uuid import UUID

import discord
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.errors import ErrorCode
from app.core.logger import get_logger
from app.schemas.article import ArticleSchema
from app.services.base import BaseService
from app.services.lock_manager import LockManager
from app.services.supabase_service import SupabaseService

logger = get_logger(__name__)


class NotificationChannel:
    """Represents a notification channel configuration."""

    def __init__(self, type: str, enabled: bool):
        """
        Initialize a notification channel.

        Args:
            type: Channel type ('discord_dm' or 'email')
            enabled: Whether the channel is enabled
        """
        self.type = type
        self.enabled = enabled


class EmailContent:
    """Represents email content with both HTML and text formats."""

    def __init__(self, html: str, text: str):
        """
        Initialize email content.

        Args:
            html: HTML formatted content
            text: Plain text content
        """
        self.html = html
        self.text = text


class NotificationResult:
    """Represents the result of a notification delivery attempt."""

    def __init__(self, success: bool, channel: str, error: Optional[str] = None):
        """
        Initialize notification result.

        Args:
            success: Whether the notification was successful
            channel: Channel used for notification
            error: Error message if failed
        """
        self.success = success
        self.channel = channel
        self.error = error


class NotificationService(BaseService):
    """
    Service for orchestrating notification delivery across multiple channels.

    This service handles:
    - Discord DM notifications through existing bot integration
    - Email notifications with HTML and text formats
    - Retry logic for failed deliveries
    - Integration with LockManager to prevent duplicates
    - User preference-based channel selection

    Requirements: 9.1, 9.2, 9.3, 9.4, 9.5, 10.6
    """

    def __init__(
        self,
        bot: Optional[discord.Client] = None,
        supabase_service: Optional[SupabaseService] = None,
        lock_manager: Optional[LockManager] = None,
        smtp_host: str = "localhost",
        smtp_port: int = 587,
        smtp_username: Optional[str] = None,
        smtp_password: Optional[str] = None,
        from_email: str = "noreply@technews.com",
    ):
        """
        Initialize the NotificationService.

        Args:
            bot: Discord bot instance for DM sending
            supabase_service: Supabase service for database operations
            lock_manager: Lock manager for preventing duplicates
            smtp_host: SMTP server host
            smtp_port: SMTP server port
            smtp_username: SMTP username
            smtp_password: SMTP password
            from_email: From email address
        """
        super().__init__()
        self.bot = bot
        self.supabase_service = supabase_service or SupabaseService()
        self.lock_manager = lock_manager or LockManager(self.supabase_service.client)

        # Email configuration
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.smtp_username = smtp_username
        self.smtp_password = smtp_password
        self.from_email = from_email

        self.logger = get_logger(f"{__name__}.NotificationService")

    async def send_notification(
        self,
        user_id: UUID,
        channels: List[NotificationChannel],
        subject: str = "Tech News Digest",
        articles: Optional[List[ArticleSchema]] = None,
        notification_type: str = "weekly_digest",
    ) -> List[NotificationResult]:
        """
        Send notification to user across specified channels.

        Args:
            user_id: User ID to send notification to
            channels: List of notification channels to use
            subject: Notification subject/title
            articles: Articles to include in notification
            notification_type: Type of notification for locking

        Returns:
            List[NotificationResult]: Results for each channel attempt

        Requirements: 9.1, 10.6
        """
        try:
            self.logger.info(
                "Starting notification delivery",
                user_id=str(user_id),
                channels=[c.type for c in channels if c.enabled],
                notification_type=notification_type,
            )

            # Get user data
            user_data = await self._get_user_data(user_id)
            if not user_data:
                self.logger.warning("User not found", user_id=str(user_id))
                return [NotificationResult(False, "all", "User not found")]

            # Check for notification lock to prevent duplicates
            scheduled_time = datetime.utcnow()
            lock = await self.lock_manager.acquire_notification_lock(
                user_id=user_id, notification_type=notification_type, scheduled_time=scheduled_time
            )

            if not lock:
                self.logger.info(
                    "Notification already processed or locked",
                    user_id=str(user_id),
                    notification_type=notification_type,
                )
                return [NotificationResult(False, "all", "Notification already processed")]

            results = []

            try:
                # Send to each enabled channel
                for channel in channels:
                    if not channel.enabled:
                        continue

                    if channel.type == "discord_dm":
                        result = await self._send_discord_dm(user_data, subject, articles)
                        results.append(result)
                    elif channel.type == "email":
                        result = await self._send_email_notification(user_data, subject, articles)
                        results.append(result)
                    else:
                        self.logger.warning(f"Unknown channel type: {channel.type}")
                        results.append(
                            NotificationResult(False, channel.type, "Unknown channel type")
                        )

                # Check if any notification succeeded
                any_success = any(result.success for result in results)

                # Release lock with appropriate status
                await self.lock_manager.release_lock(
                    lock.id, "completed" if any_success else "failed"
                )

                self.logger.info(
                    "Notification delivery completed",
                    user_id=str(user_id),
                    successful_channels=[r.channel for r in results if r.success],
                    failed_channels=[r.channel for r in results if not r.success],
                )

                return results

            except Exception as e:
                # Release lock as failed
                await self.lock_manager.release_lock(lock.id, "failed")
                raise e

        except Exception as e:
            self._handle_error(
                e,
                "Failed to send notification",
                error_code=ErrorCode.INTERNAL_ERROR,
                context={
                    "user_id": str(user_id),
                    "channels": [c.type for c in channels],
                    "notification_type": notification_type,
                },
            )

    async def send_discord_dm(self, user_id: UUID, message: str) -> bool:
        """
        Send Discord DM to user.

        Args:
            user_id: User ID to send DM to
            message: Message content

        Returns:
            bool: True if successful, False otherwise

        Requirements: 9.2
        """
        try:
            user_data = await self._get_user_data(user_id)
            if not user_data or not user_data.get("discord_id"):
                self.logger.warning("User or Discord ID not found", user_id=str(user_id))
                return False

            result = await self._send_discord_dm_raw(user_data["discord_id"], message)
            return result.success

        except Exception as e:
            self.logger.error(f"Failed to send Discord DM to user {user_id}: {e}", exc_info=True)
            return False

    async def send_email(self, user_id: UUID, subject: str, content: EmailContent) -> bool:
        """
        Send email to user.

        Args:
            user_id: User ID to send email to
            subject: Email subject
            content: Email content (HTML and text)

        Returns:
            bool: True if successful, False otherwise

        Requirements: 9.3, 9.4
        """
        try:
            user_data = await self._get_user_data(user_id)
            if not user_data or not user_data.get("email"):
                self.logger.warning("User or email not found", user_id=str(user_id))
                return False

            result = await self._send_email_raw(user_data["email"], subject, content)
            return result.success

        except Exception as e:
            self.logger.error(f"Failed to send email to user {user_id}: {e}", exc_info=True)
            return False

    # Private helper methods

    async def _get_user_data(self, user_id: UUID) -> Optional[Dict]:
        """Get user data from database."""
        try:
            response = (
                self.supabase_service.client.table("users")
                .select("id, discord_id")
                .eq("id", str(user_id))
                .execute()
            )

            if response.data and len(response.data) > 0:
                return response.data[0]
            return None

        except Exception as e:
            self.logger.error(f"Failed to get user data: {e}", exc_info=True)
            return None

    async def _send_discord_dm(
        self, user_data: Dict, subject: str, articles: Optional[List[ArticleSchema]]
    ) -> NotificationResult:
        """Send Discord DM notification."""
        try:
            discord_id = user_data.get("discord_id")
            if not discord_id:
                return NotificationResult(False, "discord_dm", "No Discord ID")

            # Check if DM notifications are enabled
            if not user_data.get("dm_notifications_enabled", True):
                return NotificationResult(False, "discord_dm", "DM notifications disabled")

            if articles:
                # Create digest embed
                embed = self._create_digest_embed(articles, subject)
                result = await self._send_discord_dm_embed(discord_id, embed)
            else:
                # Send simple message
                result = await self._send_discord_dm_raw(discord_id, subject)

            return result

        except Exception as e:
            self.logger.error(f"Failed to send Discord DM: {e}", exc_info=True)
            return NotificationResult(False, "discord_dm", str(e))

    @retry(
        stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10), reraise=True
    )
    async def _send_discord_dm_raw(self, discord_id: str, message: str) -> NotificationResult:
        """Send raw Discord DM with retry logic."""
        try:
            if not self.bot:
                return NotificationResult(False, "discord_dm", "Bot not available")

            # Validate discord_id format
            if not discord_id.isdigit():
                return NotificationResult(False, "discord_dm", "Invalid Discord ID format")

            user = await self.bot.fetch_user(int(discord_id))
            if not user:
                return NotificationResult(False, "discord_dm", "Discord user not found")

            await user.send(message)

            self.logger.info(f"Successfully sent Discord DM to user {discord_id}")
            return NotificationResult(True, "discord_dm")

        except discord.Forbidden:
            error_msg = "User has DMs disabled or bot is blocked"
            self.logger.warning(f"Cannot send DM to user {discord_id}: {error_msg}")
            return NotificationResult(False, "discord_dm", error_msg)
        except discord.HTTPException as e:
            error_msg = f"Discord HTTP error: {e}"
            self.logger.error(f"HTTP error sending DM to user {discord_id}: {e}")
            return NotificationResult(False, "discord_dm", error_msg)
        except Exception as e:
            error_msg = f"Unexpected error: {e}"
            self.logger.error(f"Failed to send DM to user {discord_id}: {e}", exc_info=True)
            return NotificationResult(False, "discord_dm", error_msg)

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def _send_discord_dm_embed(
        self, discord_id: str, embed: discord.Embed
    ) -> NotificationResult:
        """Send Discord DM with embed and retry logic."""
        try:
            if not self.bot:
                return NotificationResult(False, "discord_dm", "Bot not available")

            # Validate discord_id format
            if not discord_id.isdigit():
                return NotificationResult(False, "discord_dm", "Invalid Discord ID format")

            user = await self.bot.fetch_user(int(discord_id))
            if not user:
                return NotificationResult(False, "discord_dm", "Discord user not found")

            await user.send(embed=embed)

            self.logger.info(f"Successfully sent Discord DM embed to user {discord_id}")
            return NotificationResult(True, "discord_dm")

        except discord.Forbidden:
            error_msg = "User has DMs disabled or bot is blocked"
            self.logger.warning(f"Cannot send DM to user {discord_id}: {error_msg}")
            return NotificationResult(False, "discord_dm", error_msg)
        except discord.HTTPException as e:
            error_msg = f"Discord HTTP error: {e}"
            self.logger.error(f"HTTP error sending DM to user {discord_id}: {e}")
            return NotificationResult(False, "discord_dm", error_msg)
        except Exception as e:
            error_msg = f"Unexpected error: {e}"
            self.logger.error(f"Failed to send DM embed to user {discord_id}: {e}", exc_info=True)
            return NotificationResult(False, "discord_dm", error_msg)

    def _create_digest_embed(self, articles: List[ArticleSchema], title: str) -> discord.Embed:
        """Create Discord embed for article digest."""
        embed = discord.Embed(
            title=f"📰 {title}",
            description=f"為你精選了 {len(articles)} 篇技術文章",
            color=discord.Color.blue(),
            timestamp=datetime.utcnow(),
        )

        # Group articles by category
        categories = {}
        for article in articles:
            category = article.category or "其他"
            if category not in categories:
                categories[category] = []
            categories[category].append(article)

        # Add fields for each category (max 5 categories)
        for category, cat_articles in list(categories.items())[:5]:
            articles_text = ""
            for article in cat_articles[:5]:  # Max 5 articles per category
                # Truncate title
                title = article.title[:80] + "..." if len(article.title) > 80 else article.title
                tinkering = "⭐" * (article.tinkering_index or 3)
                articles_text += f"{tinkering} [{title}]({article.url})\n"

            embed.add_field(name=f"📂 {category}", value=articles_text or "無文章", inline=False)

        embed.set_footer(text="💡 使用 /news_now 查看完整列表 | 使用 /notifications 管理通知設定")
        return embed

    async def _send_email_notification(
        self, user_data: Dict, subject: str, articles: Optional[List[ArticleSchema]]
    ) -> NotificationResult:
        """Send email notification."""
        try:
            email = user_data.get("email")
            if not email:
                return NotificationResult(False, "email", "No email address")

            # Check if email notifications are enabled
            if not user_data.get("email_notifications_enabled", False):
                return NotificationResult(False, "email", "Email notifications disabled")

            # Create email content
            if articles:
                content = self._create_email_content(articles, subject)
            else:
                content = EmailContent(
                    html=f"<h1>{subject}</h1><p>This is a test notification.</p>",
                    text=f"{subject}\n\nThis is a test notification.",
                )

            result = await self._send_email_raw(email, subject, content)
            return result

        except Exception as e:
            self.logger.error(f"Failed to send email notification: {e}", exc_info=True)
            return NotificationResult(False, "email", str(e))

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def _send_email_raw(
        self, to_email: str, subject: str, content: EmailContent
    ) -> NotificationResult:
        """Send raw email with retry logic."""
        try:
            # Create message
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = self.from_email
            msg["To"] = to_email

            # Create text and HTML parts
            text_part = MIMEText(content.text, "plain", "utf-8")
            html_part = MIMEText(content.html, "html", "utf-8")

            # Add parts to message
            msg.attach(text_part)
            msg.attach(html_part)

            # Send email
            await self._send_smtp_email(msg)

            self.logger.info(f"Successfully sent email to {to_email}")
            return NotificationResult(True, "email")

        except Exception as e:
            error_msg = f"Failed to send email: {e}"
            self.logger.error(f"Failed to send email to {to_email}: {e}", exc_info=True)
            return NotificationResult(False, "email", error_msg)

    async def _send_smtp_email(self, msg: MIMEMultipart) -> None:
        """Send email via SMTP."""

        def _send_sync():
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                if self.smtp_username and self.smtp_password:
                    server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)

        # Run SMTP operation in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, _send_sync)

    def _create_email_content(self, articles: List[ArticleSchema], title: str) -> EmailContent:
        """Create email content with HTML and text formats."""
        # HTML content
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>{title}</title>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .header {{ background-color: #2c3e50; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; }}
                .category {{ margin-bottom: 30px; }}
                .category h3 {{ color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 5px; }}
                .article {{ margin-bottom: 15px; padding: 10px; border-left: 3px solid #3498db; }}
                .article-title {{ font-weight: bold; margin-bottom: 5px; }}
                .article-link {{ color: #3498db; text-decoration: none; }}
                .article-link:hover {{ text-decoration: underline; }}
                .tinkering {{ color: #f39c12; }}
                .footer {{ background-color: #ecf0f1; padding: 15px; text-align: center; font-size: 12px; color: #7f8c8d; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>📰 {title}</h1>
                <p>為你精選了 {len(articles)} 篇技術文章</p>
            </div>
            <div class="content">
        """

        # Text content
        text_content = f"{title}\n{'=' * len(title)}\n\n為你精選了 {len(articles)} 篇技術文章\n\n"

        # Group articles by category
        categories = {}
        for article in articles:
            category = article.category or "其他"
            if category not in categories:
                categories[category] = []
            categories[category].append(article)

        # Add content for each category
        for category, cat_articles in list(categories.items())[:5]:
            html_content += f'<div class="category"><h3>📂 {category}</h3>'
            text_content += f"\n📂 {category}\n{'-' * (len(category) + 3)}\n"

            for article in cat_articles[:5]:  # Max 5 articles per category
                tinkering = "⭐" * (article.tinkering_index or 3)

                # HTML version
                html_content += f"""
                <div class="article">
                    <div class="article-title">
                        <span class="tinkering">{tinkering}</span>
                        <a href="{article.url}" class="article-link">{article.title}</a>
                    </div>
                </div>
                """

                # Text version
                text_content += f"{tinkering} {article.title}\n{article.url}\n\n"

            html_content += "</div>"

        html_content += """
            </div>
            <div class="footer">
                <p>💡 這是你的個人化技術文章摘要</p>
                <p>如需調整通知設定，請使用 Discord 機器人或網頁界面</p>
            </div>
        </body>
        </html>
        """

        text_content += "\n" + "=" * 50 + "\n"
        text_content += "💡 這是你的個人化技術文章摘要\n"
        text_content += "如需調整通知設定，請使用 Discord 機器人或網頁界面\n"

        return EmailContent(html=html_content, text=text_content)
