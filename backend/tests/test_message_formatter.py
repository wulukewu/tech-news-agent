"""
Unit tests for MessageFormatter

Tests cover:
- web_to_discord: HTML <br> conversion, HTML tag stripping
- discord_to_web: Discord __underline__ conversion, passthrough of other syntax
- truncate_for_platform: within-limit passthrough, truncation with "...", unsupported platform
- split_for_discord: short text passthrough, paragraph/newline/word/hard splits
- format_attachment_for_web: Markdown link output
- format_attachment_for_discord: Discord link output
- validate_message: empty, too long, invalid chars, valid messages
- strip_html_tags: module-level utility
- normalize_whitespace: module-level utility

Validates: Requirements 2.5
"""

from __future__ import annotations

import pytest

from app.utils.message_formatter import (
    DISCORD_MAX_LENGTH,
    WEB_MAX_LENGTH,
    MessageFormatter,
    normalize_whitespace,
    strip_html_tags,
)

# ---------------------------------------------------------------------------
# strip_html_tags (module-level utility)
# ---------------------------------------------------------------------------


class TestStripHtmlTags:
    def test_removes_bold_tags(self):
        assert strip_html_tags("<b>Hello</b>") == "Hello"

    def test_removes_br_tag(self):
        assert strip_html_tags("line1<br/>line2") == "line1line2"

    def test_removes_multiple_tags(self):
        result = strip_html_tags("<p><strong>Hi</strong></p>")
        assert result == "Hi"

    def test_plain_text_unchanged(self):
        assert strip_html_tags("Hello world") == "Hello world"

    def test_empty_string(self):
        assert strip_html_tags("") == ""

    def test_only_tags_returns_empty(self):
        assert strip_html_tags("<div></div>") == ""

    def test_preserves_content_between_tags(self):
        assert strip_html_tags("<u>underline</u>") == "underline"


# ---------------------------------------------------------------------------
# normalize_whitespace (module-level utility)
# ---------------------------------------------------------------------------


class TestNormalizeWhitespace:
    def test_collapses_multiple_spaces(self):
        assert normalize_whitespace("hello   world") == "hello world"

    def test_collapses_tabs(self):
        assert normalize_whitespace("hello\t\tworld") == "hello world"

    def test_collapses_excessive_newlines(self):
        assert normalize_whitespace("a\n\n\n\nb") == "a\n\nb"

    def test_strips_leading_trailing_whitespace(self):
        assert normalize_whitespace("  hello  ") == "hello"

    def test_preserves_double_newline(self):
        result = normalize_whitespace("para1\n\npara2")
        assert result == "para1\n\npara2"

    def test_empty_string(self):
        assert normalize_whitespace("") == ""

    def test_only_whitespace_returns_empty(self):
        assert normalize_whitespace("   \n\n  ") == ""


# ---------------------------------------------------------------------------
# web_to_discord
# ---------------------------------------------------------------------------


class TestWebToDiscord:
    def test_br_tag_converted_to_newline(self):
        result = MessageFormatter.web_to_discord("Hello<br/>world")
        assert result == "Hello\nworld"

    def test_br_tag_without_slash(self):
        result = MessageFormatter.web_to_discord("Hello<br>world")
        assert result == "Hello\nworld"

    def test_br_tag_with_space(self):
        result = MessageFormatter.web_to_discord("Hello<br />world")
        assert result == "Hello\nworld"

    def test_html_tags_stripped(self):
        result = MessageFormatter.web_to_discord("<b>bold</b> text")
        assert result == "bold text"

    def test_bold_markdown_preserved(self):
        result = MessageFormatter.web_to_discord("**bold** text")
        assert result == "**bold** text"

    def test_italic_markdown_preserved(self):
        result = MessageFormatter.web_to_discord("*italic* text")
        assert result == "*italic* text"

    def test_strikethrough_preserved(self):
        result = MessageFormatter.web_to_discord("~~strike~~ text")
        assert result == "~~strike~~ text"

    def test_inline_code_preserved(self):
        result = MessageFormatter.web_to_discord("`code`")
        assert result == "`code`"

    def test_code_block_preserved(self):
        result = MessageFormatter.web_to_discord("```python\nprint('hi')\n```")
        assert result == "```python\nprint('hi')\n```"

    def test_plain_text_unchanged(self):
        result = MessageFormatter.web_to_discord("Hello world")
        assert result == "Hello world"

    def test_empty_string(self):
        assert MessageFormatter.web_to_discord("") == ""

    def test_multiple_br_tags(self):
        result = MessageFormatter.web_to_discord("a<br/>b<br/>c")
        assert result == "a\nb\nc"

    def test_mixed_html_and_markdown(self):
        result = MessageFormatter.web_to_discord("<b>bold</b> and **also bold**<br/>newline")
        assert result == "bold and **also bold**\nnewline"


# ---------------------------------------------------------------------------
# discord_to_web
# ---------------------------------------------------------------------------


class TestDiscordToWeb:
    def test_underline_converted_to_html(self):
        result = MessageFormatter.discord_to_web("Hello __world__")
        assert result == "Hello <u>world</u>"

    def test_multiple_underlines(self):
        result = MessageFormatter.discord_to_web("__a__ and __b__")
        assert result == "<u>a</u> and <u>b</u>"

    def test_bold_preserved(self):
        result = MessageFormatter.discord_to_web("**bold**")
        assert result == "**bold**"

    def test_italic_preserved(self):
        result = MessageFormatter.discord_to_web("*italic*")
        assert result == "*italic*"

    def test_strikethrough_preserved(self):
        result = MessageFormatter.discord_to_web("~~strike~~")
        assert result == "~~strike~~"

    def test_inline_code_preserved(self):
        result = MessageFormatter.discord_to_web("`code`")
        assert result == "`code`"

    def test_code_block_preserved(self):
        result = MessageFormatter.discord_to_web("```\ncode\n```")
        assert result == "```\ncode\n```"

    def test_plain_text_unchanged(self):
        result = MessageFormatter.discord_to_web("Hello world")
        assert result == "Hello world"

    def test_empty_string(self):
        assert MessageFormatter.discord_to_web("") == ""

    def test_newlines_preserved(self):
        result = MessageFormatter.discord_to_web("line1\nline2")
        assert result == "line1\nline2"

    def test_underline_with_spaces_inside(self):
        result = MessageFormatter.discord_to_web("__hello world__")
        assert result == "<u>hello world</u>"


# ---------------------------------------------------------------------------
# truncate_for_platform
# ---------------------------------------------------------------------------


class TestTruncateForPlatform:
    def test_short_discord_message_unchanged(self):
        text = "Hello"
        assert MessageFormatter.truncate_for_platform(text, "discord") == text

    def test_short_web_message_unchanged(self):
        text = "Hello"
        assert MessageFormatter.truncate_for_platform(text, "web") == text

    def test_discord_message_at_limit_unchanged(self):
        text = "a" * DISCORD_MAX_LENGTH
        result = MessageFormatter.truncate_for_platform(text, "discord")
        assert result == text

    def test_discord_message_over_limit_truncated(self):
        text = "a" * (DISCORD_MAX_LENGTH + 100)
        result = MessageFormatter.truncate_for_platform(text, "discord")
        assert len(result) == DISCORD_MAX_LENGTH
        assert result.endswith("...")

    def test_web_message_over_limit_truncated(self):
        text = "b" * (WEB_MAX_LENGTH + 100)
        result = MessageFormatter.truncate_for_platform(text, "web")
        assert len(result) == WEB_MAX_LENGTH
        assert result.endswith("...")

    def test_unsupported_platform_raises(self):
        with pytest.raises(ValueError, match="Unsupported platform"):
            MessageFormatter.truncate_for_platform("text", "telegram")

    def test_truncated_length_exactly_at_limit(self):
        text = "x" * (DISCORD_MAX_LENGTH + 1)
        result = MessageFormatter.truncate_for_platform(text, "discord")
        assert len(result) == DISCORD_MAX_LENGTH

    def test_truncation_suffix_present(self):
        text = "z" * (DISCORD_MAX_LENGTH + 50)
        result = MessageFormatter.truncate_for_platform(text, "discord")
        assert result[-3:] == "..."


# ---------------------------------------------------------------------------
# split_for_discord
# ---------------------------------------------------------------------------


class TestSplitForDiscord:
    def test_short_text_returns_single_chunk(self):
        text = "Hello world"
        chunks = MessageFormatter.split_for_discord(text)
        assert chunks == [text]

    def test_text_at_limit_returns_single_chunk(self):
        text = "a" * DISCORD_MAX_LENGTH
        chunks = MessageFormatter.split_for_discord(text)
        assert len(chunks) == 1
        assert chunks[0] == text

    def test_all_chunks_within_limit(self):
        text = "a" * (DISCORD_MAX_LENGTH * 3)
        chunks = MessageFormatter.split_for_discord(text)
        assert all(len(c) <= DISCORD_MAX_LENGTH for c in chunks)

    def test_content_preserved_after_split(self):
        # Hard-split case: no whitespace
        text = "a" * (DISCORD_MAX_LENGTH * 2 + 500)
        chunks = MessageFormatter.split_for_discord(text)
        assert "".join(chunks) == text

    def test_splits_on_paragraph_boundary(self):
        para = "word " * 300  # ~1500 chars per paragraph
        text = para.strip() + "\n\n" + para.strip()
        chunks = MessageFormatter.split_for_discord(text)
        assert len(chunks) >= 2
        assert all(len(c) <= DISCORD_MAX_LENGTH for c in chunks)

    def test_splits_on_newline(self):
        line = "word " * 200 + "\n"  # ~1001 chars per line
        text = line * 3
        chunks = MessageFormatter.split_for_discord(text)
        assert all(len(c) <= DISCORD_MAX_LENGTH for c in chunks)

    def test_splits_on_word_boundary(self):
        # Single long line with spaces, no newlines
        text = ("hello " * 400).strip()  # ~2400 chars
        chunks = MessageFormatter.split_for_discord(text)
        assert len(chunks) >= 2
        assert all(len(c) <= DISCORD_MAX_LENGTH for c in chunks)

    def test_empty_string_returns_single_empty_chunk(self):
        chunks = MessageFormatter.split_for_discord("")
        assert chunks == [""]

    def test_multiple_chunks_cover_all_content(self):
        text = "Hello world! " * 200  # ~2600 chars
        chunks = MessageFormatter.split_for_discord(text)
        combined = " ".join(chunks) if len(chunks) > 1 else chunks[0]
        # All words from original should appear somewhere in chunks
        assert "Hello" in combined
        assert "world" in combined


# ---------------------------------------------------------------------------
# format_attachment_for_web
# ---------------------------------------------------------------------------


class TestFormatAttachmentForWeb:
    def test_returns_markdown_link(self):
        attachment = {
            "url": "https://example.com/file.pdf",
            "filename": "report.pdf",
            "type": "application/pdf",
        }
        result = MessageFormatter.format_attachment_for_web(attachment)
        assert result == "[report.pdf](https://example.com/file.pdf)"

    def test_image_attachment(self):
        attachment = {
            "url": "https://cdn.example.com/img.png",
            "filename": "screenshot.png",
            "type": "image/png",
        }
        result = MessageFormatter.format_attachment_for_web(attachment)
        assert result == "[screenshot.png](https://cdn.example.com/img.png)"

    def test_missing_filename_uses_default(self):
        attachment = {"url": "https://example.com/file", "type": "text/plain"}
        result = MessageFormatter.format_attachment_for_web(attachment)
        assert result == "[attachment](https://example.com/file)"

    def test_missing_url_uses_empty_string(self):
        attachment = {"filename": "file.txt", "type": "text/plain"}
        result = MessageFormatter.format_attachment_for_web(attachment)
        assert result == "[file.txt]()"

    def test_format_is_markdown_link_syntax(self):
        attachment = {"url": "https://x.com/a", "filename": "a.txt", "type": "text"}
        result = MessageFormatter.format_attachment_for_web(attachment)
        assert result.startswith("[")
        assert "](https://x.com/a)" in result


# ---------------------------------------------------------------------------
# format_attachment_for_discord
# ---------------------------------------------------------------------------


class TestFormatAttachmentForDiscord:
    def test_returns_discord_link(self):
        attachment = {
            "url": "https://example.com/file.pdf",
            "filename": "report.pdf",
            "type": "application/pdf",
        }
        result = MessageFormatter.format_attachment_for_discord(attachment)
        assert result == "[report.pdf](https://example.com/file.pdf)"

    def test_image_attachment(self):
        attachment = {
            "url": "https://cdn.example.com/img.png",
            "filename": "screenshot.png",
            "type": "image/png",
        }
        result = MessageFormatter.format_attachment_for_discord(attachment)
        assert result == "[screenshot.png](https://cdn.example.com/img.png)"

    def test_missing_filename_uses_default(self):
        attachment = {"url": "https://example.com/file", "type": "text/plain"}
        result = MessageFormatter.format_attachment_for_discord(attachment)
        assert result == "[attachment](https://example.com/file)"

    def test_web_and_discord_attachment_format_identical(self):
        """Both platforms use the same [name](url) Markdown link syntax."""
        attachment = {
            "url": "https://example.com/doc.txt",
            "filename": "doc.txt",
            "type": "text/plain",
        }
        web = MessageFormatter.format_attachment_for_web(attachment)
        discord = MessageFormatter.format_attachment_for_discord(attachment)
        assert web == discord


# ---------------------------------------------------------------------------
# validate_message
# ---------------------------------------------------------------------------


class TestValidateMessage:
    def test_valid_discord_message(self):
        is_valid, error = MessageFormatter.validate_message("Hello!", "discord")
        assert is_valid is True
        assert error is None

    def test_valid_web_message(self):
        is_valid, error = MessageFormatter.validate_message("Hello world!", "web")
        assert is_valid is True
        assert error is None

    def test_empty_string_invalid(self):
        is_valid, error = MessageFormatter.validate_message("", "discord")
        assert is_valid is False
        assert error is not None
        assert "empty" in error.lower()

    def test_whitespace_only_invalid(self):
        is_valid, error = MessageFormatter.validate_message("   \n\t  ", "web")
        assert is_valid is False
        assert error is not None

    def test_discord_message_over_limit_invalid(self):
        text = "a" * (DISCORD_MAX_LENGTH + 1)
        is_valid, error = MessageFormatter.validate_message(text, "discord")
        assert is_valid is False
        assert error is not None
        assert "2000" in error

    def test_web_message_over_limit_invalid(self):
        text = "b" * (WEB_MAX_LENGTH + 1)
        is_valid, error = MessageFormatter.validate_message(text, "web")
        assert is_valid is False
        assert error is not None
        assert "50000" in error

    def test_discord_message_at_limit_valid(self):
        text = "a" * DISCORD_MAX_LENGTH
        is_valid, error = MessageFormatter.validate_message(text, "discord")
        assert is_valid is True
        assert error is None

    def test_web_message_at_limit_valid(self):
        text = "b" * WEB_MAX_LENGTH
        is_valid, error = MessageFormatter.validate_message(text, "web")
        assert is_valid is True
        assert error is None

    def test_invalid_control_characters(self):
        # Null byte is an invalid control character
        text = "Hello\x00world"
        is_valid, error = MessageFormatter.validate_message(text, "discord")
        assert is_valid is False
        assert error is not None
        assert "invalid" in error.lower()

    def test_tab_and_newline_are_valid(self):
        # Tab (\t) and newline (\n) are valid whitespace
        text = "Hello\tworld\nbye"
        is_valid, error = MessageFormatter.validate_message(text, "discord")
        assert is_valid is True
        assert error is None

    def test_unsupported_platform_raises(self):
        with pytest.raises(ValueError, match="Unsupported platform"):
            MessageFormatter.validate_message("Hello", "telegram")

    def test_valid_message_with_markdown(self):
        text = "**bold** and *italic* and `code`"
        is_valid, error = MessageFormatter.validate_message(text, "discord")
        assert is_valid is True
        assert error is None

    def test_valid_message_with_unicode(self):
        text = "你好世界 🌍"
        is_valid, error = MessageFormatter.validate_message(text, "web")
        assert is_valid is True
        assert error is None


# ---------------------------------------------------------------------------
# Round-trip conversion tests
# ---------------------------------------------------------------------------


class TestRoundTrip:
    def test_web_to_discord_to_web_plain_text(self):
        """Plain text should survive a round-trip without changes."""
        original = "Hello world, this is a test message."
        discord_fmt = MessageFormatter.web_to_discord(original)
        web_fmt = MessageFormatter.discord_to_web(discord_fmt)
        assert web_fmt == original

    def test_discord_underline_survives_discord_to_web(self):
        """Discord underline becomes <u> in web format."""
        discord_text = "__underlined__"
        web_text = MessageFormatter.discord_to_web(discord_text)
        assert "<u>underlined</u>" == web_text

    def test_br_tag_becomes_newline_in_discord(self):
        web_text = "line1<br/>line2"
        discord_text = MessageFormatter.web_to_discord(web_text)
        assert "\n" in discord_text
        assert "<br" not in discord_text
