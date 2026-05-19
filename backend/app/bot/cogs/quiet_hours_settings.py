"""
通知設定指令 Cog

提供使用者管理 DM 通知偏好的指令，包括個人化通知頻率設定。
"""

import discord
from discord import app_commands
from discord.ext import commands

from app.core.logger import get_logger
from app.services.supabase_service import SupabaseService

logger = get_logger(__name__)


class QuietHoursSettings(commands.Cog):
    """Discord Cog for quiet hours notification commands."""

    def __init__(self, bot: commands.Bot, supabase_service: SupabaseService = None):
        self.bot = bot
        self.supabase_service = supabase_service or SupabaseService()

    # Quiet Hours Commands

    @app_commands.command(name="quiet-hours", description="查看你的勿擾時段設定")
    async def quiet_hours(self, interaction: discord.Interaction):
        """查看目前的勿擾時段設定"""
        await interaction.response.defer(ephemeral=True)

        logger.info(
            "Command /quiet-hours triggered",
            user_id=str(interaction.user.id),
            command="quiet-hours",
        )

        try:
            from app.services.quiet_hours_service import QuietHoursService

            discord_id = str(interaction.user.id)
            user_uuid = await self.supabase_service.get_or_create_user(discord_id)

            quiet_hours_service = QuietHoursService(self.supabase_service)
            quiet_hours = await quiet_hours_service.get_quiet_hours(user_uuid)

            if not quiet_hours:
                # Create default quiet hours
                quiet_hours = await quiet_hours_service.create_default_quiet_hours(user_uuid)

            # Check current status
            is_in_quiet_hours, _ = await quiet_hours_service.is_in_quiet_hours(user_uuid)

            embed = discord.Embed(
                title="🌙 勿擾時段設定",
                color=discord.Color.purple(),
            )

            # Status
            status_emoji = "🔕" if is_in_quiet_hours else "🔔"
            status_text = "目前在勿擾時段內" if is_in_quiet_hours else "目前不在勿擾時段內"

            embed.add_field(
                name=f"{status_emoji} 目前狀態",
                value=f"**{status_text}**\n啟用狀態：{'✅ 已啟用' if quiet_hours.enabled else '❌ 已停用'}",
                inline=False,
            )

            if quiet_hours.enabled:
                # Time range
                embed.add_field(
                    name="⏰ 時間範圍",
                    value=f"{quiet_hours.start_time.strftime('%H:%M')} - {quiet_hours.end_time.strftime('%H:%M')}",
                    inline=True,
                )

                # Timezone
                embed.add_field(
                    name="🌍 時區",
                    value=quiet_hours.timezone,
                    inline=True,
                )

                # Weekdays
                weekday_names = ["", "週一", "週二", "週三", "週四", "週五", "週六", "週日"]
                active_days = [weekday_names[day] for day in quiet_hours.weekdays]
                embed.add_field(
                    name="📅 適用日期",
                    value=" ".join(active_days) if len(active_days) < 7 else "每天",
                    inline=False,
                )

                embed.add_field(
                    name="ℹ️ 說明",
                    value="在勿擾時段內，所有通知將被暫停。通知會在勿擾時段結束後恢復發送。",
                    inline=False,
                )
            else:
                embed.add_field(
                    name="ℹ️ 說明",
                    value="勿擾時段目前已停用。使用 `/set-quiet-hours` 來設定勿擾時段。",
                    inline=False,
                )

            await interaction.followup.send(embed=embed, ephemeral=True)
            logger.info("Quiet hours displayed successfully", user_id=discord_id)

        except Exception as e:
            logger.error(
                "Failed to display quiet hours",
                user_id=str(interaction.user.id),
                command="quiet-hours",
                error=str(e),
                exc_info=True,
            )
            await interaction.followup.send(
                "❌ 載入勿擾時段設定時發生錯誤，請稍後再試。",
                ephemeral=True,
            )

    @app_commands.command(name="set-quiet-hours", description="設定勿擾時段（彈出表單）")
    async def set_quiet_hours(self, interaction: discord.Interaction):
        """開啟勿擾時段設定表單"""
        from app.bot.ui.modals import SetQuietHoursModal

        logger.info(
            "Command /set-quiet-hours triggered (modal)",
            user_id=str(interaction.user.id),
            command="set-quiet-hours",
        )
        await interaction.response.send_modal(SetQuietHoursModal(self.supabase_service))

    @app_commands.command(name="toggle-quiet-hours", description="快速開啟或關閉勿擾時段")
    async def toggle_quiet_hours(self, interaction: discord.Interaction):
        """快速切換勿擾時段的啟用狀態"""
        await interaction.response.defer(ephemeral=True)

        logger.info(
            "Command /toggle-quiet-hours triggered",
            user_id=str(interaction.user.id),
            command="toggle-quiet-hours",
        )

        try:
            from app.services.quiet_hours_service import QuietHoursService

            discord_id = str(interaction.user.id)
            user_uuid = await self.supabase_service.get_or_create_user(discord_id)

            quiet_hours_service = QuietHoursService(self.supabase_service)
            quiet_hours = await quiet_hours_service.get_quiet_hours(user_uuid)

            if not quiet_hours:
                # Create default quiet hours (disabled)
                quiet_hours = await quiet_hours_service.create_default_quiet_hours(user_uuid)

            # Toggle enabled status
            new_enabled = not quiet_hours.enabled
            updated_quiet_hours = await quiet_hours_service.update_quiet_hours(
                user_id=user_uuid,
                enabled=new_enabled,
            )

            # Create response embed
            embed = discord.Embed(
                title="🌙 勿擾時段狀態已切換",
                color=discord.Color.green() if new_enabled else discord.Color.orange(),
            )

            status_text = "✅ 已啟用" if new_enabled else "❌ 已停用"
            embed.add_field(
                name="📊 新狀態",
                value=f"勿擾時段：{status_text}",
                inline=False,
            )

            if new_enabled:
                embed.add_field(
                    name="⏰ 時間設定",
                    value=f"• 時間：{updated_quiet_hours.start_time.strftime('%H:%M')} - {updated_quiet_hours.end_time.strftime('%H:%M')}\n• 時區：{updated_quiet_hours.timezone}",
                    inline=False,
                )
                embed.add_field(
                    name="ℹ️ 說明",
                    value="在勿擾時段內，所有通知將被暫停。",
                    inline=False,
                )
            else:
                embed.add_field(
                    name="ℹ️ 說明",
                    value="勿擾時段已停用，你將正常接收所有通知。",
                    inline=False,
                )

            await interaction.followup.send(embed=embed, ephemeral=True)
            logger.info(
                "Quiet hours toggled successfully",
                user_id=discord_id,
                new_enabled=new_enabled,
            )

        except Exception as e:
            logger.error(
                "Failed to toggle quiet hours",
                user_id=str(interaction.user.id),
                command="toggle-quiet-hours",
                error=str(e),
                exc_info=True,
            )
            await interaction.followup.send(
                "❌ 切換勿擾時段狀態時發生錯誤，請稍後再試。",
                ephemeral=True,
            )


async def setup(bot: commands.Bot):
    await bot.add_cog(QuietHoursSettings(bot))
