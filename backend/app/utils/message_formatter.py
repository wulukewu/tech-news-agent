"""
Platform Message Formatter

Handles conversion between Web Markdown and Discord message formats,
enforces platform-specific length limits, processes attachments, and
validates message content.

Key capabilities:
- Web Markdown ↔ Discord format conversion
- Platform-specific length truncation and message splitting
- Attachment formatting for web and Discord
- Message validation with descriptive error messages
- HTML tag stripping and whitespace normalisation

Validates: Requirements 2.5
"""

from __future__ import annotations

import re
from typing import Optional

from app.core.logger import get_logger

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DISCORD_MAX_LENGTH: int = 2000
WEB_MAX_LENGTH: int = 50000

_PLATFORM_WEB = "web"
_PLATFORM_DISCORD = "discord"
_SUPPORTED_PLATFORMS = {_PLATFORM_WEB, _PLATFORM_DISCORD}

# Characters that are invalid in message content (control characters except
# common whitespace: tab, newline, carriage return)
_INVALID_CHAR_PATTERN = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")

# HTML tag pattern
_HTML_TAG_PATTERN = re.compile(r"<[^>]+>")

# Multiple-whitespace patterns (preserves single spaces and newlines)
_MULTI_SPACE_PATTERN = re.compile(r"[ \t]+")
_MULTI_NEWLINE_PATTERN = re.compile(r"\n{3,}")

# Discord underline: __text__
_DISCORD_UNDERLINE_PATTERN = re.compile(r"__(.+?)__", re.DOTALL)

# HTML <br> / <br /> tags used in web Markdown
_HTML_BR_PATTERN = re.compile(r"<br\s*/?>", re.IGNORECASE)

# Truncation suffix
_TRUNCATION_SUFFIX = "..."


# ---------------------------------------------------------------------------
# Module-level utility functions
# ---------------------------------------------------------------------------


def strip_html_tags(text: str) -> str:
    """Remove all HTML tags from *text*.

    Args:
        text: Input string that may contain HTML tags.

    Returns:
        String with all HTML tags removed.

    Example:
        >>> strip_html_tags("<b>Hello</b> <br/> world")
        'Hello  world'
    """
    return _HTML_TAG_PATTERN.sub("", text)


def normalize_whitespace(text: str) -> str:
    """Normalise multiple consecutive spaces/tabs and excessive newlines.

    - Collapses runs of spaces/tabs into a single space.
    - Collapses three or more consecutive newlines into two newlines.
    - Strips leading and trailing whitespace.

    Args:
        text: Input string with potentially irregular whitespace.

    Returns:
        Normalised string.

    Example:
        >>> normalize_whitespace("hello   world\\n\\n\\n\\nbye")
        'hello world\\n\\nbye'
    """
    # Collapse horizontal whitespace
    text = _MULTI_SPACE_PATTERN.sub(" ", text)
    # Collapse excessive newlines
    text = _MULTI_NEWLINE_PATTERN.sub("\n\n", text)
    return text.strip()


# ---------------------------------------------------------------------------
# MessageFormatter class
# ---------------------------------------------------------------------------


class MessageFormatter:
    """Utility class for converting and validating messages across platforms.

    Provides static/class methods for:
    - Converting between Web Markdown and Discord message formats.
    - Truncating or splitting messages to fit platform length limits.
    - Formatting attachment metadata for each platform.
    - Validating message content against platform constraints.

    All methods are stateless and can be called without instantiation, but
    the class is provided for organisational clarity and potential future
    extension.

    Validates: Requirements 2.5
    """

    # ------------------------------------------------------------------
    # Format conversion
    # ------------------------------------------------------------------

    @staticmethod
    def web_to_discord(text: str) -> str:
        """Convert Web Markdown text to Discord-compatible format.

        Key transformations applied:
        - ``<br>`` / ``<br/>`` HTML line-break tags → ``\\n``
        - Other HTML tags are stripped entirely.
        - No other Markdown syntax changes are needed because Discord
          supports ``**bold**``, ``*italic*``, ``~~strikethrough~~``,
          and `` `code` `` natively.

        Args:
            text: Web Markdown string, potentially containing HTML tags.

        Returns:
            Discord-compatible string.

        Example:
            >>> MessageFormatter.web_to_discord("Hello<br/>world")
            'Hello\\nworld'
        """
        logger.debug("Converting web format to Discord", text_length=len(text))

        # Replace <br> tags with newlines before stripping other HTML
        result = _HTML_BR_PATTERN.sub("\n", text)

        # Strip any remaining HTML tags
        result = strip_html_tags(result)

        logger.debug("Web-to-Discord conversion complete", result_length=len(result))
        return result

    @staticmethod
    def discord_to_web(text: str) -> str:
        """Convert Discord-formatted text to Web Markdown.

        Key transformations applied:
        - Discord ``__underline__`` → HTML ``<u>underline</u>`` (since
          standard Markdown does not have an underline syntax).
        - All other Discord Markdown syntax (``**bold**``, ``*italic*``,
          ``~~strikethrough~~``, `` `code` ``, ` ```code block``` `) is
          already valid Markdown and is left unchanged.

        Args:
            text: Discord-formatted string.

        Returns:
            Web Markdown string.

        Example:
            >>> MessageFormatter.discord_to_web("Hello __world__")
            'Hello <u>world</u>'
        """
        logger.debug("Converting Discord format to web", text_length=len(text))

        # Convert Discord underline to HTML underline tag
        result = _DISCORD_UNDERLINE_PATTERN.sub(r"<u>\1</u>", text)

        logger.debug("Discord-to-web conversion complete", result_length=len(result))
        return result

    # ------------------------------------------------------------------
    # Length limits
    # ------------------------------------------------------------------

    @staticmethod
    def truncate_for_platform(text: str, platform: str) -> str:
        """Truncate *text* to the platform's maximum length if necessary.

        If the text exceeds the platform limit, it is truncated and
        ``"..."`` is appended so the total length equals the limit.

        Args:
            text: Message text to potentially truncate.
            platform: Target platform — ``"web"`` or ``"discord"``.

        Returns:
            Original text if within limits, otherwise truncated text
            ending with ``"..."``.

        Raises:
            ValueError: If *platform* is not a supported platform.

        Example:
            >>> MessageFormatter.truncate_for_platform("a" * 2005, "discord")
            'a' * 1997 + '...'
        """
        if platform not in _SUPPORTED_PLATFORMS:
            raise ValueError(
                f"Unsupported platform: {platform!r}. "
                f"Must be one of {sorted(_SUPPORTED_PLATFORMS)}"
            )

        max_length = DISCORD_MAX_LENGTH if platform == _PLATFORM_DISCORD else WEB_MAX_LENGTH

        if len(text) <= max_length:
            return text

        logger.debug(
            "Truncating message for platform",
            platform=platform,
            original_length=len(text),
            max_length=max_length,
        )

        truncated = text[: max_length - len(_TRUNCATION_SUFFIX)] + _TRUNCATION_SUFFIX
        return truncated

    @staticmethod
    def split_for_discord(text: str) -> list[str]:
        """Split *text* into chunks that each fit within Discord's 2000-char limit.

        The algorithm tries to split on paragraph boundaries (``\\n\\n``),
        then on single newlines, and finally on word boundaries (spaces)
        before falling back to a hard character split.  This preserves
        readability as much as possible.

        Args:
            text: Message text to split.

        Returns:
            List of strings, each at most ``DISCORD_MAX_LENGTH`` characters.
            Returns a list with the original text if it already fits.

        Example:
            >>> chunks = MessageFormatter.split_for_discord("a" * 4500)
            >>> all(len(c) <= 2000 for c in chunks)
            True
        """
        if len(text) <= DISCORD_MAX_LENGTH:
            return [text]

        logger.debug(
            "Splitting message for Discord",
            total_length=len(text),
            max_chunk_size=DISCORD_MAX_LENGTH,
        )

        chunks: list[str] = []
        remaining = text

        while len(remaining) > DISCORD_MAX_LENGTH:
            chunk = remaining[:DISCORD_MAX_LENGTH]

            # Try to split on paragraph boundary (double newline)
            split_pos = chunk.rfind("\n\n")
            if split_pos > 0:
                chunk = remaining[: split_pos + 2]
                remaining = remaining[split_pos + 2 :]
                chunks.append(chunk.rstrip())
                remaining = remaining.lstrip()
                continue

            # Try to split on single newline
            split_pos = chunk.rfind("\n")
            if split_pos > 0:
                chunk = remaining[: split_pos + 1]
                remaining = remaining[split_pos + 1 :]
                chunks.append(chunk.rstrip())
                remaining = remaining.lstrip()
                continue

            # Try to split on word boundary (space)
            split_pos = chunk.rfind(" ")
            if split_pos > 0:
                chunk = remaining[:split_pos]
                remaining = remaining[split_pos + 1 :]
                chunks.append(chunk)
                continue

            # Hard split as last resort
            chunks.append(remaining[:DISCORD_MAX_LENGTH])
            remaining = remaining[DISCORD_MAX_LENGTH:]

        if remaining:
            chunks.append(remaining)

        logger.debug("Message split into chunks", chunk_count=len(chunks))
        return chunks

    # ------------------------------------------------------------------
    # Attachment handling
    # ------------------------------------------------------------------

    @staticmethod
    def format_attachment_for_web(attachment: dict) -> str:
        """Format an attachment dict as a Markdown link for web display.

        Args:
            attachment: Dict with keys:
                - ``url`` (str): Direct URL to the attachment.
                - ``filename`` (str): Human-readable filename.
                - ``type`` (str): MIME type or category (e.g. ``"image/png"``).

        Returns:
            Markdown-formatted link string: ``[filename](url)``.

        Example:
            >>> MessageFormatter.format_attachment_for_web(
            ...     {"url": "https://example.com/file.pdf",
            ...      "filename": "report.pdf", "type": "application/pdf"}
            ... )
            '[report.pdf](https://example.com/file.pdf)'
        """
        url: str = attachment.get("url", "")
        filename: str = attachment.get("filename", "attachment")

        logger.debug("Formatting attachment for web", filename=filename, url=url)
        return f"[{filename}]({url})"

    @staticmethod
    def format_attachment_for_discord(attachment: dict) -> str:
        """Format an attachment dict as a Discord-compatible link.

        Discord renders plain URLs as embeds/previews automatically.
        This method returns a labelled link using Discord's Markdown syntax.

        Args:
            attachment: Dict with keys:
                - ``url`` (str): Direct URL to the attachment.
                - ``filename`` (str): Human-readable filename.
                - ``type`` (str): MIME type or category.

        Returns:
            Discord-formatted link string: ``[filename](url)``.

        Example:
            >>> MessageFormatter.format_attachment_for_discord(
            ...     {"url": "https://example.com/img.png",
            ...      "filename": "screenshot.png", "type": "image/png"}
            ... )
            '[screenshot.png](https://example.com/img.png)'
        """
        url: str = attachment.get("url", "")
        filename: str = attachment.get("filename", "attachment")

        logger.debug("Formatting attachment for Discord", filename=filename, url=url)
        return f"[{filename}]({url})"

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    @staticmethod
    def validate_message(text: str, platform: str) -> tuple[bool, Optional[str]]:
        """Validate a message for a given platform.

        Checks performed:
        1. Message is not empty (after stripping whitespace).
        2. Message length is within the platform's maximum limit.
        3. Message does not contain invalid control characters.

        Args:
            text: Message text to validate.
            platform: Target platform — ``"web"`` or ``"discord"``.

        Returns:
            A ``(is_valid, error_message)`` tuple.  ``error_message`` is
            ``None`` when ``is_valid`` is ``True``.

        Raises:
            ValueError: If *platform* is not a supported platform.

        Example:
            >>> MessageFormatter.validate_message("Hello!", "discord")
            (True, None)
            >>> MessageFormatter.validate_message("", "web")
            (False, 'Message cannot be empty')
        """
        if platform not in _SUPPORTED_PLATFORMS:
            raise ValueError(
                f"Unsupported platform: {platform!r}. "
                f"Must be one of {sorted(_SUPPORTED_PLATFORMS)}"
            )

        # Check for empty message
        if not text or not text.strip():
            logger.debug("Message validation failed: empty message", platform=platform)
            return False, "Message cannot be empty"

        # Check length limit
        max_length = DISCORD_MAX_LENGTH if platform == _PLATFORM_DISCORD else WEB_MAX_LENGTH
        if len(text) > max_length:
            error = (
                f"Message exceeds {platform} length limit "
                f"({len(text)} > {max_length} characters)"
            )
            logger.debug(
                "Message validation failed: too long",
                platform=platform,
                length=len(text),
                max_length=max_length,
            )
            return False, error

        # Check for invalid characters
        if _INVALID_CHAR_PATTERN.search(text):
            logger.debug("Message validation failed: invalid characters", platform=platform)
            return False, "Message contains invalid control characters"

        logger.debug(
            "Message validation passed",
            platform=platform,
            length=len(text),
        )
        return True, None
