"""
通知設定指令 Cog

提供使用者管理 DM 通知偏好的指令，包括個人化通知頻率設定。
"""

import discord
from discord import app_commands
from discord.ext import commands

from app.core.exceptions import SupabaseServiceError
from app.core.logger import get_logger
from app.core.timezone_converter import TimezoneConverter
from app.repositories.user_notification_preferences import UserNotificationPreferencesRepository
from app.schemas.user_notification_preferences import UpdateUserNotificationPreferencesRequest
from app.services.preference_service import PreferenceService
from app.services.supabase_service import SupabaseService
from app.tasks.scheduler import get_dynamic_scheduler

logger = get_logger(__name__)


class NotificationSettings(commands.Cog):
    """通知設定指令群組 with service layer dependency injection"""

    def __init__(self, bot: commands.Bot, supabase_service: SupabaseService = None):
        """
        Initialize NotificationSettings cog with service dependencies.

        Args:
            bot: Discord bot instance
            supabase_service: Optional SupabaseService instance for dependency injection
        """
        self.bot = bot
        self.supabase_service = supabase_service or SupabaseService()

    @app_commands.command(name="notifications", description="管理你的 DM 通知設定")
    @app_commands.describe(enabled="是否接收 DM 通知（開啟/關閉）")
    @app_commands.choices(
        enabled=[
            app_commands.Choice(name="開啟通知", value=1),
            app_commands.Choice(name="關閉通知", value=0),
        ]
    )
    async def notifications(
        self, interaction: discord.Interaction, enabled: app_commands.Choice[int]
    ):
        """設定是否接收新文章的 DM 通知"""
        await interaction.response.defer(ephemeral=True)

        logger.info(
            "Command /notifications triggered",
            user_id=str(interaction.user.id),
            command="notifications",
            enabled=bool(enabled.value),
        )

        try:
            discord_id = str(interaction.user.id)
            is_enabled = bool(enabled.value)

            # 更新通知設定 via service layer
            await self.supabase_service.update_notification_settings(discord_id, is_enabled)

            # 回應使用者
            status_text = "✅ 已開啟" if is_enabled else "❌ 已關閉"
            embed = discord.Embed(
                title="🔔 通知設定已更新",
                description=f"DM 通知狀態：{status_text}",
                color=discord.Color.green() if is_enabled else discord.Color.red(),
            )

            if is_enabled:
                embed.add_field(
                    name="📬 你將會收到",
                    value="• 每週新文章推薦\n• 訂閱來源的最新內容\n• 個人化的閱讀建議",
                    inline=False,
                )
                embed.set_footer(text="💡 提示：確保你的 DM 設定允許接收來自伺服器成員的訊息")
            else:
                embed.add_field(
                    name="ℹ️ 注意",
                    value="你將不會收到任何 DM 通知，但仍可使用 `/news_now` 查看文章",
                    inline=False,
                )

            await interaction.followup.send(embed=embed, ephemeral=True)

            logger.info(
                "Notification settings updated successfully",
                user_id=discord_id,
                is_enabled=is_enabled,
            )

        except SupabaseServiceError as e:
            logger.error(
                "Failed to update notification settings",
                user_id=str(interaction.user.id),
                command="notifications",
                error=str(e),
                exc_info=True,
            )
            await interaction.followup.send(
                "❌ 更新通知設定時發生錯誤，請稍後再試。\n" "💡 建議：資料庫連線可能暫時中斷，請稍後再試或聯繫管理員。",
                ephemeral=True,
            )
        except Exception as e:
            logger.critical(
                "Unexpected error in notifications command",
                user_id=str(interaction.user.id),
                command="notifications",
                error=str(e),
                error_type=type(e).__name__,
                exc_info=True,
            )
            await interaction.followup.send(
                "❌ 發生未預期的錯誤，請稍後再試。\n" "💡 建議：如果問題持續發生，請聯繫管理員並提供你的使用者 ID。",
                ephemeral=True,
            )

    @app_commands.command(name="notification_status", description="查看你目前的通知設定")
    async def notification_status(self, interaction: discord.Interaction):
        """查看目前的通知設定狀態"""
        await interaction.response.defer(ephemeral=True)

        logger.info(
            "Command /notification_status triggered",
            user_id=str(interaction.user.id),
            command="notification_status",
        )

        try:
            discord_id = str(interaction.user.id)

            # 查詢通知設定 via service layer
            is_enabled = await self.supabase_service.get_notification_settings(discord_id)

            # 建立回應
            status_text = "✅ 已開啟" if is_enabled else "❌ 已關閉"
            status_color = discord.Color.green() if is_enabled else discord.Color.red()

            embed = discord.Embed(
                title="🔔 你的通知設定",
                description=f"DM 通知狀態：{status_text}",
                color=status_color,
            )

            if is_enabled:
                embed.add_field(
                    name="📬 你正在接收",
                    value="• 每週新文章推薦\n• 訂閱來源的最新內容\n• 個人化的閱讀建議",
                    inline=False,
                )
            else:
                embed.add_field(
                    name="ℹ️ 目前狀態",
                    value="你不會收到 DM 通知\n使用 `/notifications` 來開啟通知",
                    inline=False,
                )

            embed.set_footer(text="使用 /notifications 來變更設定")

            await interaction.followup.send(embed=embed, ephemeral=True)
            logger.info(
                "Notification status sent successfully", user_id=discord_id, is_enabled=is_enabled
            )

        except SupabaseServiceError as e:
            logger.error(
                "Failed to get notification settings",
                user_id=str(interaction.user.id),
                command="notification_status",
                error=str(e),
                exc_info=True,
            )
            await interaction.followup.send(
                "❌ 查詢通知設定時發生錯誤，請稍後再試。\n" "💡 建議：資料庫連線可能暫時中斷，請稍後再試或聯繫管理員。",
                ephemeral=True,
            )
        except Exception as e:
            logger.critical(
                "Unexpected error in notification_status command",
                user_id=str(interaction.user.id),
                command="notification_status",
                error=str(e),
                error_type=type(e).__name__,
                exc_info=True,
            )
            await interaction.followup.send(
                "❌ 發生未預期的錯誤，請稍後再試。\n" "💡 建議：如果問題持續發生，請聯繫管理員並提供你的使用者 ID。",
                ephemeral=True,
            )

    # Personalized Notification Frequency Commands

    @app_commands.command(name="notification-settings", description="查看你的個人化通知設定")
    async def notification_settings_detailed(self, interaction: discord.Interaction):
        """查看個人化通知設定詳情"""
        await interaction.response.defer(ephemeral=True)

        logger.info(
            "Command /notification-settings triggered",
            user_id=str(interaction.user.id),
            command="notification-settings",
        )

        try:
            discord_id = str(interaction.user.id)

            # Get user UUID
            user_id = await self.supabase_service.get_or_create_user(discord_id)

            # Initialize services
            prefs_repo = UserNotificationPreferencesRepository(self.supabase_service.client)
            preference_service = PreferenceService(prefs_repo)

            # Get notification preferences
            preferences = await preference_service.get_user_preferences(user_id)

            # Create embed
            embed = discord.Embed(
                title="🔔 你的個人化通知設定",
                color=discord.Color.blue(),
            )

            # Status
            status_emoji = "✅" if preferences.dm_enabled else "❌"
            embed.add_field(
                name="📱 Discord DM",
                value=f"{status_emoji} {'已開啟' if preferences.dm_enabled else '已關閉'}",
                inline=True,
            )

            email_emoji = "✅" if preferences.email_enabled else "❌"
            embed.add_field(
                name="📧 電子郵件",
                value=f"{email_emoji} {'已開啟' if preferences.email_enabled else '已關閉（即將推出）'}",
                inline=True,
            )

            # Frequency
            frequency_map = {
                "daily": "每日",
                "weekly": "每週",
                "monthly": "每月",
                "disabled": "停用",
            }
            embed.add_field(
                name="⏰ 通知頻率",
                value=frequency_map.get(preferences.frequency, preferences.frequency),
                inline=True,
            )

            # Time and timezone
            if preferences.frequency != "disabled":
                embed.add_field(
                    name="🕐 通知時間",
                    value=f"{preferences.notification_time.strftime('%H:%M')}",
                    inline=True,
                )

                embed.add_field(
                    name="🌍 時區",
                    value=preferences.timezone,
                    inline=True,
                )

                # Calculate next notification time
                try:
                    next_time = TimezoneConverter.get_next_notification_time(
                        frequency=preferences.frequency,
                        notification_time=preferences.notification_time.strftime("%H:%M"),
                        timezone=preferences.timezone,
                    )

                    if next_time:
                        local_time = TimezoneConverter.convert_to_user_time(
                            next_time, preferences.timezone
                        )
                        embed.add_field(
                            name="📅 下次通知",
                            value=f"{local_time.strftime('%Y-%m-%d %H:%M')}",
                            inline=True,
                        )
                except Exception as e:
                    logger.warning(f"Failed to calculate next notification time: {e}")

            embed.set_footer(text="使用其他指令來修改這些設定")

            await interaction.followup.send(embed=embed, ephemeral=True)
            logger.info("Notification settings displayed successfully", user_id=discord_id)

        except Exception as e:
            logger.error(
                "Failed to get notification settings",
                user_id=str(interaction.user.id),
                command="notification-settings",
                error=str(e),
                exc_info=True,
            )
            await interaction.followup.send(
                "❌ 查詢通知設定時發生錯誤，請稍後再試。",
                ephemeral=True,
            )

    @app_commands.command(name="set-notification-frequency", description="設定通知頻率")
    @app_commands.describe(frequency="選擇通知頻率")
    @app_commands.choices(
        frequency=[
            app_commands.Choice(name="每日", value="daily"),
            app_commands.Choice(name="每週", value="weekly"),
            app_commands.Choice(name="每月", value="monthly"),
            app_commands.Choice(name="停用", value="disabled"),
        ]
    )
    async def set_notification_frequency(
        self, interaction: discord.Interaction, frequency: app_commands.Choice[str]
    ):
        """設定通知頻率"""
        await interaction.response.defer(ephemeral=True)

        logger.info(
            "Command /set-notification-frequency triggered",
            user_id=str(interaction.user.id),
            command="set-notification-frequency",
            frequency=frequency.value,
        )

        try:
            discord_id = str(interaction.user.id)

            # Get user UUID
            user_id = await self.supabase_service.get_or_create_user(discord_id)

            # Initialize services
            prefs_repo = UserNotificationPreferencesRepository(self.supabase_service.client)
            preference_service = PreferenceService(prefs_repo)
            dynamic_scheduler = get_dynamic_scheduler()

            # Update preferences
            updates = UpdateUserNotificationPreferencesRequest(frequency=frequency.value)
            updated_preferences = await preference_service.update_preferences(
                user_id, updates, source="discord"
            )

            # Create response
            frequency_map = {
                "daily": "每日",
                "weekly": "每週",
                "monthly": "每月",
                "disabled": "停用",
            }

            embed = discord.Embed(
                title="✅ 通知頻率已更新",
                description=f"通知頻率已設定為：**{frequency_map[frequency.value]}**",
                color=discord.Color.green(),
            )

            if frequency.value != "disabled":
                embed.add_field(
                    name="ℹ️ 提醒",
                    value="你可以使用 `/set-notification-time` 來調整通知時間",
                    inline=False,
                )

            await interaction.followup.send(embed=embed, ephemeral=True)
            logger.info(
                "Notification frequency updated successfully",
                user_id=discord_id,
                frequency=frequency.value,
            )

        except Exception as e:
            logger.error(
                "Failed to update notification frequency",
                user_id=str(interaction.user.id),
                command="set-notification-frequency",
                error=str(e),
                exc_info=True,
            )
            await interaction.followup.send(
                "❌ 更新通知頻率時發生錯誤，請稍後再試。",
                ephemeral=True,
            )

    @app_commands.command(name="set-notification-time", description="設定通知時間")
    @app_commands.describe(hour="小時 (0-23)", minute="分鐘 (0-59)")
    async def set_notification_time(
        self,
        interaction: discord.Interaction,
        hour: app_commands.Range[int, 0, 23],
        minute: app_commands.Range[int, 0, 59] = 0,
    ):
        """設定通知時間"""
        await interaction.response.defer(ephemeral=True)

        logger.info(
            "Command /set-notification-time triggered",
            user_id=str(interaction.user.id),
            command="set-notification-time",
            hour=hour,
            minute=minute,
        )

        try:
            discord_id = str(interaction.user.id)

            # Get user UUID
            user_id = await self.supabase_service.get_or_create_user(discord_id)

            # Initialize services
            prefs_repo = UserNotificationPreferencesRepository(self.supabase_service.client)
            preference_service = PreferenceService(prefs_repo)
            dynamic_scheduler = get_dynamic_scheduler()

            # Format time
            notification_time = f"{hour:02d}:{minute:02d}"

            # Update preferences
            updates = UpdateUserNotificationPreferencesRequest(notification_time=notification_time)
            updated_preferences = await preference_service.update_preferences(
                user_id, updates, source="discord"
            )

            # Create response
            embed = discord.Embed(
                title="✅ 通知時間已更新",
                description=f"通知時間已設定為：**{notification_time}**",
                color=discord.Color.green(),
            )

            embed.add_field(
                name="🌍 時區",
                value=f"目前時區：{updated_preferences.timezone}",
                inline=False,
            )

            embed.add_field(
                name="ℹ️ 提醒",
                value="你可以使用 `/set-timezone` 來調整時區設定",
                inline=False,
            )

            await interaction.followup.send(embed=embed, ephemeral=True)
            logger.info(
                "Notification time updated successfully", user_id=discord_id, time=notification_time
            )

        except Exception as e:
            logger.error(
                "Failed to update notification time",
                user_id=str(interaction.user.id),
                command="set-notification-time",
                error=str(e),
                exc_info=True,
            )
            await interaction.followup.send(
                "❌ 更新通知時間時發生錯誤，請稍後再試。",
                ephemeral=True,
            )

    @app_commands.command(name="set-timezone", description="設定時區")
    @app_commands.describe(timezone="選擇時區")
    @app_commands.choices(
        timezone=[
            app_commands.Choice(name="台北 (Asia/Taipei)", value="Asia/Taipei"),
            app_commands.Choice(name="東京 (Asia/Tokyo)", value="Asia/Tokyo"),
            app_commands.Choice(name="上海 (Asia/Shanghai)", value="Asia/Shanghai"),
            app_commands.Choice(name="香港 (Asia/Hong_Kong)", value="Asia/Hong_Kong"),
            app_commands.Choice(name="新加坡 (Asia/Singapore)", value="Asia/Singapore"),
            app_commands.Choice(name="紐約 (America/New_York)", value="America/New_York"),
            app_commands.Choice(name="洛杉磯 (America/Los_Angeles)", value="America/Los_Angeles"),
            app_commands.Choice(name="芝加哥 (America/Chicago)", value="America/Chicago"),
            app_commands.Choice(name="倫敦 (Europe/London)", value="Europe/London"),
            app_commands.Choice(name="巴黎 (Europe/Paris)", value="Europe/Paris"),
            app_commands.Choice(name="柏林 (Europe/Berlin)", value="Europe/Berlin"),
            app_commands.Choice(name="雪梨 (Australia/Sydney)", value="Australia/Sydney"),
            app_commands.Choice(name="UTC", value="UTC"),
        ]
    )
    async def set_timezone(
        self, interaction: discord.Interaction, timezone: app_commands.Choice[str]
    ):
        """設定時區"""
        await interaction.response.defer(ephemeral=True)

        logger.info(
            "Command /set-timezone triggered",
            user_id=str(interaction.user.id),
            command="set-timezone",
            timezone=timezone.value,
        )

        try:
            discord_id = str(interaction.user.id)

            # Get user UUID
            user_id = await self.supabase_service.get_or_create_user(discord_id)

            # Initialize services
            prefs_repo = UserNotificationPreferencesRepository(self.supabase_service.client)
            preference_service = PreferenceService(prefs_repo)
            dynamic_scheduler = get_dynamic_scheduler()

            # Update preferences
            updates = UpdateUserNotificationPreferencesRequest(timezone=timezone.value)
            updated_preferences = await preference_service.update_preferences(
                user_id, updates, source="discord"
            )

            # Create response
            embed = discord.Embed(
                title="✅ 時區已更新",
                description=f"時區已設定為：**{timezone.name}**",
                color=discord.Color.green(),
            )

            embed.add_field(
                name="🕐 通知時間",
                value=f"目前通知時間：{updated_preferences.notification_time.strftime('%H:%M')}",
                inline=False,
            )

            # Calculate next notification time
            try:
                next_time = TimezoneConverter.get_next_notification_time(
                    frequency=updated_preferences.frequency,
                    notification_time=updated_preferences.notification_time.strftime("%H:%M"),
                    timezone=updated_preferences.timezone,
                )

                if next_time:
                    local_time = TimezoneConverter.convert_to_user_time(
                        next_time, updated_preferences.timezone
                    )
                    embed.add_field(
                        name="📅 下次通知",
                        value=f"{local_time.strftime('%Y-%m-%d %H:%M')}",
                        inline=False,
                    )
            except Exception as e:
                logger.warning(f"Failed to calculate next notification time: {e}")

            await interaction.followup.send(embed=embed, ephemeral=True)
            logger.info(
                "Timezone updated successfully", user_id=discord_id, timezone=timezone.value
            )

        except Exception as e:
            logger.error(
                "Failed to update timezone",
                user_id=str(interaction.user.id),
                command="set-timezone",
                error=str(e),
                exc_info=True,
            )
            await interaction.followup.send(
                "❌ 更新時區時發生錯誤，請稍後再試。",
                ephemeral=True,
            )

    @app_commands.command(name="toggle-notifications", description="快速開啟或關閉通知")
    async def toggle_notifications(self, interaction: discord.Interaction):
        """快速切換通知開關"""
        await interaction.response.defer(ephemeral=True)

        logger.info(
            "Command /toggle-notifications triggered",
            user_id=str(interaction.user.id),
            command="toggle-notifications",
        )

        try:
            discord_id = str(interaction.user.id)

            # Get user UUID
            user_id = await self.supabase_service.get_or_create_user(discord_id)

            # Initialize services
            prefs_repo = UserNotificationPreferencesRepository(self.supabase_service.client)
            preference_service = PreferenceService(prefs_repo)
            dynamic_scheduler = get_dynamic_scheduler()

            # Get current preferences
            current_preferences = await preference_service.get_user_preferences(user_id)

            # Toggle DM notifications
            new_dm_enabled = not current_preferences.dm_enabled
            updates = UpdateUserNotificationPreferencesRequest(dm_enabled=new_dm_enabled)
            updated_preferences = await preference_service.update_preferences(
                user_id, updates, source="discord"
            )

            # Create response
            status_emoji = "✅" if new_dm_enabled else "❌"
            status_text = "已開啟" if new_dm_enabled else "已關閉"

            embed = discord.Embed(
                title=f"{status_emoji} 通知{status_text}",
                description=f"Discord DM 通知已{status_text}",
                color=discord.Color.green() if new_dm_enabled else discord.Color.red(),
            )

            if new_dm_enabled:
                frequency_map = {
                    "daily": "每日",
                    "weekly": "每週",
                    "monthly": "每月",
                    "disabled": "停用",
                }
                embed.add_field(
                    name="📬 你將會收到",
                    value=f"• {frequency_map.get(updated_preferences.frequency, updated_preferences.frequency)} 通知\n• 時間：{updated_preferences.notification_time.strftime('%H:%M')}\n• 時區：{updated_preferences.timezone}",
                    inline=False,
                )
            else:
                embed.add_field(
                    name="ℹ️ 注意",
                    value="你將不會收到任何 DM 通知\n使用 `/toggle-notifications` 重新開啟",
                    inline=False,
                )

            await interaction.followup.send(embed=embed, ephemeral=True)
            logger.info(
                "Notifications toggled successfully", user_id=discord_id, enabled=new_dm_enabled
            )

        except Exception as e:
            logger.error(
                "Failed to toggle notifications",
                user_id=str(interaction.user.id),
                command="toggle-notifications",
                error=str(e),
                exc_info=True,
            )
            await interaction.followup.send(
                "❌ 切換通知設定時發生錯誤，請稍後再試。",
                ephemeral=True,
            )


async def setup(bot: commands.Bot):
    await bot.add_cog(NotificationSettings(bot))
