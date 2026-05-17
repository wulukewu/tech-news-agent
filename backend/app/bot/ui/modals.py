"""Discord UI Modals for multi-field input forms."""

import re
from datetime import time

import discord

from app.core.logger import get_logger

logger = get_logger(__name__)


class SetQuietHoursModal(discord.ui.Modal, title="設定勿擾時段"):
    """Modal for /set-quiet-hours — replaces the 3-parameter slash command."""

    start_time = discord.ui.TextInput(
        label="開始時間 (HH:MM)",
        placeholder="例如：22:00",
        min_length=4,
        max_length=5,
    )
    end_time = discord.ui.TextInput(
        label="結束時間 (HH:MM)",
        placeholder="例如：08:00",
        min_length=4,
        max_length=5,
    )
    enabled = discord.ui.TextInput(
        label="啟用 (yes / no)",
        placeholder="yes",
        min_length=2,
        max_length=3,
        default="yes",
    )

    def __init__(self, supabase_service):
        super().__init__()
        self.supabase_service = supabase_service

    async def on_submit(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer(ephemeral=True)

        _time_re = re.compile(r"^([01]?\d|2[0-3]):([0-5]\d)$")

        start_val = self.start_time.value.strip()
        end_val = self.end_time.value.strip()
        enabled_val = self.enabled.value.strip().lower()

        if not _time_re.match(start_val):
            await interaction.followup.send("❌ 開始時間格式錯誤，請使用 HH:MM（例如 22:00）", ephemeral=True)
            return
        if not _time_re.match(end_val):
            await interaction.followup.send("❌ 結束時間格式錯誤，請使用 HH:MM（例如 08:00）", ephemeral=True)
            return
        if enabled_val not in ("yes", "no"):
            await interaction.followup.send("❌ 啟用欄位請填 yes 或 no", ephemeral=True)
            return

        is_enabled = enabled_val == "yes"
        sh, sm = map(int, start_val.split(":"))
        eh, em = map(int, end_val.split(":"))

        try:
            from app.services.quiet_hours_service import QuietHoursService

            discord_id = str(interaction.user.id)
            user_uuid = await self.supabase_service.get_or_create_user(discord_id)
            svc = QuietHoursService(self.supabase_service)
            updated = await svc.update_quiet_hours(
                user_id=user_uuid,
                start_time=time(sh, sm),
                end_time=time(eh, em),
                enabled=is_enabled,
            )

            status = "✅ 已啟用" if is_enabled else "❌ 已停用"
            embed = discord.Embed(title="🌙 勿擾時段已更新", color=discord.Color.green())
            embed.add_field(name="狀態", value=status, inline=True)
            if is_enabled:
                embed.add_field(name="時間", value=f"{start_val} – {end_val}", inline=True)
                embed.add_field(name="時區", value=updated.timezone, inline=True)
            await interaction.followup.send(embed=embed, ephemeral=True)

        except Exception as e:
            logger.error("SetQuietHoursModal error", error=str(e), exc_info=True)
            await interaction.followup.send("❌ 設定失敗，請稍後再試。", ephemeral=True)


class AddFeedModal(discord.ui.Modal, title="訂閱 RSS 來源"):
    """Modal for /add_feed — replaces the 3-parameter slash command."""

    name = discord.ui.TextInput(
        label="來源名稱",
        placeholder="例如：Hacker News",
        max_length=100,
    )
    url = discord.ui.TextInput(
        label="RSS / Atom 網址",
        placeholder="https://news.ycombinator.com/rss",
        max_length=500,
    )
    category = discord.ui.TextInput(
        label="分類",
        placeholder="例如：AI、Web、Security",
        max_length=50,
    )

    def __init__(self, supabase_service):
        super().__init__()
        self.supabase_service = supabase_service

    async def on_submit(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer(ephemeral=True)

        from app.bot.utils.validators import validate_and_sanitize_feed_data
        from app.core.exceptions import SupabaseServiceError

        is_valid, sanitized, error_msg = validate_and_sanitize_feed_data(
            self.name.value, self.url.value, self.category.value
        )
        if not is_valid:
            await interaction.followup.send(f"❌ {error_msg}", ephemeral=True)
            return

        try:
            from uuid import UUID

            discord_id = str(interaction.user.id)
            user_uuid = await self.supabase_service.get_or_create_user(discord_id)

            # Upsert feed
            resp = (
                self.supabase_service.client.table("feeds")
                .select("id")
                .eq("url", sanitized["url"])
                .execute()
            )
            if resp.data:
                feed_id = UUID(resp.data[0]["id"])
            else:
                ins = (
                    self.supabase_service.client.table("feeds")
                    .insert(
                        {
                            "name": sanitized["name"],
                            "url": sanitized["url"],
                            "category": sanitized["category"],
                            "is_active": True,
                        }
                    )
                    .execute()
                )
                feed_id = UUID(ins.data[0]["id"])

            await self.supabase_service.subscribe_to_feed(discord_id, feed_id)
            await interaction.followup.send(
                f"✅ 已訂閱 **{sanitized['name']}** ({sanitized['category']})\n🔗 {sanitized['url']}",
                ephemeral=True,
            )

        except SupabaseServiceError as e:
            if "duplicate" in str(e).lower() or "already exists" in str(e).lower():
                await interaction.followup.send(
                    f"ℹ️ 你已經訂閱過 **{self.name.value}** 了！", ephemeral=True
                )
            else:
                logger.error("AddFeedModal DB error", error=str(e), exc_info=True)
                await interaction.followup.send("❌ 訂閱失敗，請稍後再試。", ephemeral=True)
        except Exception as e:
            logger.error("AddFeedModal error", error=str(e), exc_info=True)
            await interaction.followup.send("❌ 發生未預期的錯誤，請稍後再試。", ephemeral=True)
