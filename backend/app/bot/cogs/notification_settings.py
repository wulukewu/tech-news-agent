"""
通知設定指令 Cog

提供使用者管理 DM 通知偏好的指令。
"""

import discord
from discord import app_commands
from discord.ext import commands

from app.core.exceptions import SupabaseServiceError
from app.core.logger import get_logger
from app.services.supabase_service import SupabaseService

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
                "❌ 更新通知設定時發生錯誤，請稍後再試。\n"
                "💡 建議：資料庫連線可能暫時中斷，請稍後再試或聯繫管理員。",
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
                "❌ 發生未預期的錯誤，請稍後再試。\n"
                "💡 建議：如果問題持續發生，請聯繫管理員並提供你的使用者 ID。",
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
                "❌ 查詢通知設定時發生錯誤，請稍後再試。\n"
                "💡 建議：資料庫連線可能暫時中斷，請稍後再試或聯繫管理員。",
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
                "❌ 發生未預期的錯誤，請稍後再試。\n"
                "💡 建議：如果問題持續發生，請聯繫管理員並提供你的使用者 ID。",
                ephemeral=True,
            )


async def setup(bot: commands.Bot):
    """載入 Cog with service layer dependency injection"""
    supabase_service = SupabaseService()
    await bot.add_cog(NotificationSettings(bot, supabase_service))
    logger.info("NotificationSettings cog loaded")
