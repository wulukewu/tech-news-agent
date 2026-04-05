"""
Admin commands for managing the bot and scheduler.
"""
import logging
import discord
from discord import app_commands
from discord.ext import commands

from app.tasks.scheduler import background_fetch_job, get_scheduler_health

logger = logging.getLogger(__name__)


class AdminCommands(commands.Cog):
    """Admin commands for bot management."""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
    
    @app_commands.command(
        name="trigger_fetch",
        description="手動觸發文章抓取任務 (立即執行 scheduler)"
    )
    async def trigger_fetch(self, interaction: discord.Interaction):
        """
        Manually trigger the background fetch job to fetch new articles immediately.
        
        This command allows users to manually trigger the scheduler without waiting
        for the scheduled time.
        """
        try:
            # Defer the response since the job might take a while
            await interaction.response.defer(ephemeral=True)
            
            logger.info(f"Manual scheduler trigger requested by {interaction.user.name} ({interaction.user.id})")
            
            # Import asyncio to run the job in the background
            import asyncio
            
            # Create a background task to run the job
            asyncio.create_task(background_fetch_job())
            
            # Send success message
            embed = discord.Embed(
                title="✅ 文章抓取已觸發",
                description="已手動觸發文章抓取任務，正在背景執行中...",
                color=discord.Color.green()
            )
            embed.add_field(
                name="說明",
                value="系統將立即開始抓取新文章並進行分析。\n完成後可使用 `/news_now` 查看最新文章。",
                inline=False
            )
            
            await interaction.followup.send(embed=embed, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Failed to trigger scheduler manually: {e}", exc_info=True)
            
            error_embed = discord.Embed(
                title="❌ 觸發失敗",
                description="無法觸發文章抓取任務，請稍後再試。",
                color=discord.Color.red()
            )
            
            await interaction.followup.send(embed=error_embed, ephemeral=True)
    
    @app_commands.command(
        name="scheduler_status",
        description="查看 scheduler 的執行狀態"
    )
    async def scheduler_status(self, interaction: discord.Interaction):
        """
        Get the current status of the scheduler.
        
        Shows information about the last execution, including:
        - Last execution time
        - Articles processed
        - Failed operations
        - Health status
        """
        try:
            await interaction.response.defer(ephemeral=True)
            
            # Get scheduler health data
            health_data = await get_scheduler_health()
            
            # Create embed based on health status
            if health_data["is_healthy"]:
                embed = discord.Embed(
                    title="✅ Scheduler 狀態正常",
                    color=discord.Color.green()
                )
            else:
                embed = discord.Embed(
                    title="⚠️ Scheduler 狀態異常",
                    color=discord.Color.orange()
                )
                
                # Add issues if any
                if health_data["issues"]:
                    issues_text = "\n".join(f"• {issue}" for issue in health_data["issues"])
                    embed.add_field(
                        name="問題",
                        value=issues_text,
                        inline=False
                    )
            
            # Add execution info
            if health_data["last_execution_time"]:
                embed.add_field(
                    name="上次執行時間",
                    value=f"<t:{int(__import__('datetime').datetime.fromisoformat(health_data['last_execution_time'].replace('Z', '+00:00')).timestamp())}:R>",
                    inline=True
                )
            else:
                embed.add_field(
                    name="上次執行時間",
                    value="尚未執行",
                    inline=True
                )
            
            embed.add_field(
                name="處理文章數",
                value=str(health_data["articles_processed"]),
                inline=True
            )
            
            if health_data["total_operations"] > 0:
                success_rate = ((health_data["total_operations"] - health_data["failed_operations"]) 
                               / health_data["total_operations"] * 100)
                embed.add_field(
                    name="成功率",
                    value=f"{success_rate:.1f}%",
                    inline=True
                )
            
            await interaction.followup.send(embed=embed, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Failed to get scheduler status: {e}", exc_info=True)
            
            error_embed = discord.Embed(
                title="❌ 查詢失敗",
                description="無法取得 scheduler 狀態，請稍後再試。",
                color=discord.Color.red()
            )
            
            await interaction.followup.send(embed=error_embed, ephemeral=True)


async def setup(bot: commands.Bot):
    """Register the AdminCommands cog."""
    await bot.add_cog(AdminCommands(bot))
