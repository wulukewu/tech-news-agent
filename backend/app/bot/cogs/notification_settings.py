"""
通知設定指令 Cog

提供使用者管理 DM 通知偏好的指令。
"""

import logging
import discord
from discord import app_commands
from discord.ext import commands
from app.services.supabase_service import SupabaseService
from app.core.exceptions import SupabaseServiceError

logger = logging.getLogger(__name__)


class NotificationSettings(commands.Cog):
    """通知設定指令群組"""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
    
    @app_commands.command(
        name="notifications",
        description="管理你的 DM 通知設定"
    )
    @app_commands.describe(
        enabled="是否接收 DM 通知（開啟/關閉）"
    )
    @app_commands.choices(enabled=[
        app_commands.Choice(name="開啟通知", value=1),
        app_commands.Choice(name="關閉通知", value=0)
    ])
    async def notifications(
        self,
        interaction: discord.Interaction,
        enabled: app_commands.Choice[int]
    ):
        """設定是否接收新文章的 DM 通知"""
        await interaction.response.defer(ephemeral=True)
        
        try:
            discord_id = str(interaction.user.id)
            is_enabled = bool(enabled.value)
            
            # 更新通知設定
            supabase = SupabaseService()
            await supabase.update_notification_settings(discord_id, is_enabled)
            
            # 回應使用者
            status_text = "✅ 已開啟" if is_enabled else "❌ 已關閉"
            embed = discord.Embed(
                title="🔔 通知設定已更新",
                description=f"DM 通知狀態：{status_text}",
                color=discord.Color.green() if is_enabled else discord.Color.red()
            )
            
            if is_enabled:
                embed.add_field(
                    name="📬 你將會收到",
                    value="• 每週新文章推薦\n• 訂閱來源的最新內容\n• 個人化的閱讀建議",
                    inline=False
                )
                embed.set_footer(text="💡 提示：確保你的 DM 設定允許接收來自伺服器成員的訊息")
            else:
                embed.add_field(
                    name="ℹ️ 注意",
                    value="你將不會收到任何 DM 通知，但仍可使用 `/news_now` 查看文章",
                    inline=False
                )
            
            await interaction.followup.send(embed=embed, ephemeral=True)
            
            logger.info(
                f"User {discord_id} updated notification settings to {is_enabled}"
            )
            
        except SupabaseServiceError as e:
            logger.error(f"Failed to update notification settings: {e}", exc_info=True)
            await interaction.followup.send(
                "❌ 更新通知設定時發生錯誤，請稍後再試。",
                ephemeral=True
            )
        except Exception as e:
            logger.error(f"Unexpected error in notifications command: {e}", exc_info=True)
            await interaction.followup.send(
                "❌ 發生未預期的錯誤，請稍後再試。",
                ephemeral=True
            )
    
    @app_commands.command(
        name="notification_status",
        description="查看你目前的通知設定"
    )
    async def notification_status(self, interaction: discord.Interaction):
        """查看目前的通知設定狀態"""
        await interaction.response.defer(ephemeral=True)
        
        try:
            discord_id = str(interaction.user.id)
            
            # 查詢通知設定
            supabase = SupabaseService()
            is_enabled = await supabase.get_notification_settings(discord_id)
            
            # 建立回應
            status_text = "✅ 已開啟" if is_enabled else "❌ 已關閉"
            status_color = discord.Color.green() if is_enabled else discord.Color.red()
            
            embed = discord.Embed(
                title="🔔 你的通知設定",
                description=f"DM 通知狀態：{status_text}",
                color=status_color
            )
            
            if is_enabled:
                embed.add_field(
                    name="📬 你正在接收",
                    value="• 每週新文章推薦\n• 訂閱來源的最新內容\n• 個人化的閱讀建議",
                    inline=False
                )
            else:
                embed.add_field(
                    name="ℹ️ 目前狀態",
                    value="你不會收到 DM 通知\n使用 `/notifications` 來開啟通知",
                    inline=False
                )
            
            embed.set_footer(text="使用 /notifications 來變更設定")
            
            await interaction.followup.send(embed=embed, ephemeral=True)
            
        except SupabaseServiceError as e:
            logger.error(f"Failed to get notification settings: {e}", exc_info=True)
            await interaction.followup.send(
                "❌ 查詢通知設定時發生錯誤，請稍後再試。",
                ephemeral=True
            )
        except Exception as e:
            logger.error(f"Unexpected error in notification_status command: {e}", exc_info=True)
            await interaction.followup.send(
                "❌ 發生未預期的錯誤，請稍後再試。",
                ephemeral=True
            )


async def setup(bot: commands.Bot):
    """載入 Cog"""
    await bot.add_cog(NotificationSettings(bot))
    logger.info("NotificationSettings cog loaded")

