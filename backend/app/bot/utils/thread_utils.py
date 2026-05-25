from __future__ import annotations

import discord


def sanitize_thread_name(name: str, fallback: str = "tech-news-discussion") -> str:
    cleaned = " ".join(name.split()).strip()
    if not cleaned:
        cleaned = fallback
    return cleaned[:90]


async def ensure_discussion_thread(
    interaction: discord.Interaction,
    thread_name: str,
) -> tuple[discord.Thread | discord.abc.Messageable, bool]:
    """Return current thread or create one from the current channel."""
    if isinstance(interaction.channel, discord.Thread):
        return interaction.channel, False

    channel = interaction.channel
    # If the channel is a DM or doesn't support threads, return the channel directly
    if (
        channel is None
        or isinstance(channel, discord.DMChannel)
        or not hasattr(channel, "create_thread")
    ):
        if channel is None:
            try:
                channel = await interaction.user.create_dm()
            except Exception:
                channel = interaction.user
        return channel, False

    cleaned_name = sanitize_thread_name(thread_name)

    try:
        thread = await channel.create_thread(
            name=cleaned_name,
            auto_archive_duration=1440,
        )
        return thread, True
    except (AttributeError, TypeError, discord.HTTPException):
        starter = await channel.send(f"🧵 已建立討論串：{cleaned_name}")
        thread = await starter.create_thread(name=cleaned_name, auto_archive_duration=1440)
        return thread, True
