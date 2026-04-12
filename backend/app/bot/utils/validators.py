"""
資料驗證模組

提供所有使用者輸入的驗證函數，確保資料符合格式要求並防止無效資料進入資料庫。
"""

import logging
import re
from uuid import UUID

logger = logging.getLogger("TechNewsAgent.validators")

# 常數定義
MAX_TITLE_LENGTH = 2000
MAX_SUMMARY_LENGTH = 5000
VALID_STATUSES = {"Unread", "Read", "Archived"}
MIN_RATING = 1
MAX_RATING = 5


def validate_feed_url(url: str) -> tuple[bool, str]:
    """
    驗證 RSS feed URL 格式

    Args:
        url: 要驗證的 URL

    Returns:
        (is_valid, error_message): 驗證結果和錯誤訊息（若有）
    """
    if not url or not isinstance(url, str):
        return False, "URL 不能為空"

    # 檢查 URL 格式
    url_pattern = re.compile(
        r"^https?://"  # http:// or https://
        r"(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|"  # domain...
        r"localhost|"  # localhost...
        r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"  # ...or ip
        r"(?::\d+)?"  # optional port
        r"(?:/?|[/?]\S+)$",
        re.IGNORECASE,
    )

    if not url_pattern.match(url):
        return False, "URL 格式無效，必須是有效的 HTTP 或 HTTPS 網址"

    # 檢查長度
    if len(url) > 2048:
        return False, "URL 長度超過限制（最多 2048 字元）"

    return True, ""


def validate_rating(rating: int) -> tuple[bool, str]:
    """
    驗證文章評分

    Args:
        rating: 評分值

    Returns:
        (is_valid, error_message): 驗證結果和錯誤訊息（若有）
    """
    if not isinstance(rating, int):
        return False, "評分必須是整數"

    if rating < MIN_RATING or rating > MAX_RATING:
        return False, f"評分必須在 {MIN_RATING} 到 {MAX_RATING} 之間"

    return True, ""


def validate_status(status: str) -> tuple[bool, str]:
    """
    驗證閱讀清單狀態

    Args:
        status: 狀態值

    Returns:
        (is_valid, error_message): 驗證結果和錯誤訊息（若有）
    """
    if not isinstance(status, str):
        return False, "狀態必須是字串"

    if status not in VALID_STATUSES:
        valid_list = ", ".join(VALID_STATUSES)
        return False, f"狀態必須是以下之一：{valid_list}"

    return True, ""


def validate_uuid(uuid_str: str) -> tuple[bool, str]:
    """
    驗證 UUID 格式

    Args:
        uuid_str: UUID 字串

    Returns:
        (is_valid, error_message): 驗證結果和錯誤訊息（若有）
    """
    if not uuid_str or not isinstance(uuid_str, str):
        return False, "UUID 不能為空"

    try:
        UUID(uuid_str)
        return True, ""
    except (ValueError, AttributeError):
        return False, "UUID 格式無效"


def truncate_text(text: str, max_length: int, field_name: str = "文字") -> str:
    """
    截斷文字到指定長度

    Args:
        text: 要截斷的文字
        max_length: 最大長度
        field_name: 欄位名稱（用於日誌）

    Returns:
        截斷後的文字
    """
    if not text:
        return text

    if len(text) > max_length:
        logger.warning(f"{field_name} 長度 {len(text)} 超過限制 {max_length}，已截斷")
        return text[:max_length]

    return text


def sanitize_title(title: str) -> str:
    """
    清理並截斷文章標題

    Args:
        title: 原始標題

    Returns:
        清理後的標題
    """
    if not title:
        return ""

    # 移除前後空白
    title = title.strip()

    # 截斷到最大長度
    return truncate_text(title, MAX_TITLE_LENGTH, "標題")


def sanitize_summary(summary: str) -> str:
    """
    清理並截斷文章摘要

    Args:
        summary: 原始摘要

    Returns:
        清理後的摘要
    """
    if not summary:
        return ""

    # 移除前後空白
    summary = summary.strip()

    # 截斷到最大長度
    return truncate_text(summary, MAX_SUMMARY_LENGTH, "摘要")


def validate_and_sanitize_feed_data(name: str, url: str, category: str) -> tuple[bool, dict, str]:
    """
    驗證並清理 feed 資料

    Args:
        name: Feed 名稱
        url: Feed URL
        category: Feed 分類

    Returns:
        (is_valid, sanitized_data, error_message)
    """
    # Strip whitespace from URL first
    url = url.strip() if url else ""

    # 驗證 URL
    is_valid, error = validate_feed_url(url)
    if not is_valid:
        return False, {}, error

    # 清理資料
    sanitized = {
        "name": sanitize_title(name),
        "url": url,
        "category": category.strip() if category else "未分類",
    }

    # 檢查必填欄位
    if not sanitized["name"]:
        return False, {}, "Feed 名稱不能為空"

    return True, sanitized, ""
