"""
Proactive DM Cog

Sends personalized article recommendations via Discord DM after each RSS fetch.
Handles inline 👍/👎 feedback buttons that update the user's preference model.
Requirements: 1.4, 2.4, 3.1-3.5
"""

import logging

import discord
from discord.ext import commands

from app.qa_agent.proactive_learning.preference_model import PreferenceModel

logger = logging.getLogger(__name__)

FEEDBACK_DELTA = 0.2  # Weight adjustment per button click


class FeedbackView(discord.ui.View):
    """Per-article 👍/👎 inline feedback buttons."""

    def __init__(self, user_id: str, category: str, article_title: str):
        super().__init__(timeout=None)
        self.user_id = user_id
        self.category = category
        self.article_title = article_title

        self.add_item(_FeedbackButton(user_id, category, True))
        self.add_item(_FeedbackButton(user_id, category, False))


class _FeedbackButton(discord.ui.Button):
    def __init__(self, user_id: str, category: str, positive: bool):
        label = "👍 多推這類" if positive else "👎 少推這類"
        style = discord.ButtonStyle.success if positive else discord.ButtonStyle.danger
        # custom_id must be unique and stable for persistence
        direction = "up" if positive else "down"
        super().__init__(
            label=label,
            style=style,
            custom_id=f"proactive_fb_{direction}_{user_id}_{category[:20]}",
        )
        self.user_id = user_id
        self.category = category
        self.positive = positive

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        delta = FEEDBACK_DELTA if self.positive else -FEEDBACK_DELTA
        try:
            pref = PreferenceModel()
            await pref.apply_adjustments(self.user_id, {self.category: delta})
        except Exception as exc:
            logger.error("Failed to update preference weight: %s", exc)
            await interaction.followup.send("❌ 更新偏好時發生錯誤，請稍後再試。", ephemeral=True)
            return

        # Disable all buttons in this view
        for item in self.view.children:
            item.disabled = True
        try:
            await interaction.message.edit(view=self.view)
        except discord.HTTPException:
            pass

        direction = "增加" if self.positive else "減少"
        await interaction.followup.send(
            f"✅ 已記錄，會{direction} **{self.category}** 的推薦頻率。",
            ephemeral=True,
        )


async def send_proactive_dm(
    bot: discord.Client,
    discord_id: str,
    articles_with_reasons: list[dict],
) -> bool:
    """
    Send a proactive recommendation DM to a user.

    Args:
        bot: The Discord bot client.
        discord_id: Target user's Discord ID.
        articles_with_reasons: List of dicts with keys:
            - article: article dict (title, url, category, ai_summary)
            - reason: str recommendation reason
            - user_id: internal UUID string

    Returns:
        True if DM was sent successfully, False otherwise.
    """
    try:
        user = await bot.fetch_user(int(discord_id))
    except (discord.NotFound, discord.HTTPException) as exc:
        logger.warning("Cannot fetch Discord user %s: %s", discord_id, exc)
        return False

    try:
        # Header message
        await user.send("📬 **今日個人化推薦** — 根據你的閱讀偏好，以下文章值得一看：")

        for item in articles_with_reasons[:5]:
            article = item["article"]
            reason = item["reason"]
            user_id = item["user_id"]
            category = (article.get("category") or "未分類").strip()

            embed = discord.Embed(
                title=article.get("title", "（無標題）")[:256],
                url=article.get("url", ""),
                color=discord.Color.blurple(),
            )
            embed.add_field(name="💡 推薦原因", value=reason, inline=False)
            if article.get("ai_summary"):
                embed.add_field(
                    name="📝 摘要",
                    value=article["ai_summary"][:300]
                    + ("…" if len(article.get("ai_summary", "")) > 300 else ""),
                    inline=False,
                )
            embed.set_footer(text=f"分類：{category}")

            view = FeedbackView(
                user_id=user_id, category=category, article_title=article.get("title", "")
            )
            await user.send(embed=embed, view=view)

        return True

    except discord.Forbidden:
        logger.warning("Cannot send DM to user %s (DMs disabled)", discord_id)
        return False
    except discord.HTTPException as exc:
        logger.error("HTTP error sending DM to %s: %s", discord_id, exc)
        return False


class ProactiveDMCog(commands.Cog):
    """Cog placeholder — actual sending is done via send_proactive_dm()."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(ProactiveDMCog(bot))
