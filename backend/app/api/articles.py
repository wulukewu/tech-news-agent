"""
文章動態 API 模組

提供個人化文章動態查詢功能，基於使用者訂閱源。
"""

from datetime import datetime, timedelta, timezone

UTC = timezone.utc
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.auth import get_current_user
from app.schemas.article import ArticleResponse
from app.schemas.responses import (
    PaginatedResponse,
    paginated_response,
    success_response,
)
from app.services.supabase_service import SupabaseService

router = APIRouter()


@router.get("/categories")
async def get_categories(current_user: dict = Depends(get_current_user)):
    """
    查詢所有可用的文章類別

    Returns:
        List[str]: 類別列表

    Raises:
        HTTPException: 500 當資料庫查詢失敗時
    """
    try:
        supabase = SupabaseService()

        # 查詢所有不重複的類別
        response = supabase.client.table("feeds").select("category").eq("is_active", True).execute()

        # 提取不重複的類別
        categories = list(set(feed["category"] for feed in response.data if feed.get("category")))
        categories.sort()

        return success_response({"categories": categories})

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve categories: {e!s}")


@router.get("/me", response_model=PaginatedResponse[ArticleResponse])
async def get_my_articles(
    page: int = Query(1, ge=1, description="頁碼（從 1 開始）"),
    page_size: int = Query(20, ge=1, le=100, description="每頁文章數（1-100）"),
    categories: str = Query(None, description="篩選類別（逗號分隔，例如：前端開發,AI 應用）"),
    current_user: dict = Depends(get_current_user),
):
    """
    查詢所有文章（可按類別篩選）

    Args:
        page: 頁碼（從 1 開始）
        page_size: 每頁文章數（1-100）
        categories: 篩選類別（逗號分隔），若為 None 則顯示所有類別
        current_user: 當前使用者資訊

    Returns:
        ArticleListResponse: 包含文章列表和分頁資訊

    Raises:
        HTTPException: 422 當分頁參數無效時
        HTTPException: 500 當資料庫查詢失敗時
    """
    try:
        supabase = SupabaseService()

        # 計算時間窗口（7 天內）
        seven_days_ago = datetime.utcnow() - timedelta(days=7)

        # 計算分頁
        offset = (page - 1) * page_size

        # 1. 先查詢用戶訂閱的 feed IDs
        subscriptions_response = (
            supabase.client.table("user_subscriptions")
            .select("feed_id")
            .eq("user_id", str(current_user["user_id"]))
            .execute()
        )

        subscribed_feed_ids = [sub["feed_id"] for sub in subscriptions_response.data]

        # 如果用戶沒有訂閱任何 feed，返回空列表
        if not subscribed_feed_ids:
            return paginated_response(items=[], total_count=0, page=page, page_size=page_size)

        # 2. 建立基礎查詢 - 只查詢用戶訂閱的 feeds 的文章
        query = (
            supabase.client.table("articles")
            .select(
                "id, title, url, published_at, tinkering_index, ai_summary, "
                "feeds!inner(name, category)"
            )
            .in_("feed_id", subscribed_feed_ids)
            .gte("published_at", seven_days_ago.isoformat())
            .not_.is_("tinkering_index", "null")
        )

        # 如果有指定類別篩選
        if categories:
            category_list = [cat.strip() for cat in categories.split(",")]
            query = query.in_("feeds.category", category_list)

        # 執行查詢
        response = (
            query.order("tinkering_index", desc=True)
            .order("published_at", desc=True)
            .range(offset, offset + page_size - 1)
            .execute()
        )

        # 計算總數
        # 如果有類別篩選，需要 join feeds 表
        if categories:
            category_list = [cat.strip() for cat in categories.split(",")]
            count_query = (
                supabase.client.table("articles")
                .select("id, feeds!inner(category)", count="exact")
                .in_("feed_id", subscribed_feed_ids)
                .gte("published_at", seven_days_ago.isoformat())
                .not_.is_("tinkering_index", "null")
                .in_("feeds.category", category_list)
            )
        else:
            count_query = (
                supabase.client.table("articles")
                .select("id", count="exact")
                .in_("feed_id", subscribed_feed_ids)
                .gte("published_at", seven_days_ago.isoformat())
                .not_.is_("tinkering_index", "null")
            )

        count_response = count_query.execute()
        total_count = count_response.count if count_response.count else 0

        # 3. 查詢用戶的 reading list 中的文章 IDs
        reading_list_response = (
            supabase.client.table("reading_list")
            .select("article_id")
            .eq("user_id", str(current_user["user_id"]))
            .execute()
        )
        reading_list_article_ids = {item["article_id"] for item in reading_list_response.data}

        # 組合回應
        articles = []
        for article in response.data:
            feed_info = article.get("feeds", {})

            # 處理 published_at - 確保包含時區資訊
            published_at = None
            if article.get("published_at"):
                try:
                    raw = article["published_at"]
                    if isinstance(raw, datetime):
                        published_at = raw if raw.tzinfo else raw.replace(tzinfo=UTC)
                    else:
                        pub_at_str = str(raw)
                        if pub_at_str.endswith("Z"):
                            pub_at_str = pub_at_str[:-1] + "+00:00"
                        published_at = datetime.fromisoformat(pub_at_str)
                except (ValueError, TypeError):
                    published_at = None

            # 檢查文章是否在 reading list 中
            is_in_reading_list = article["id"] in reading_list_article_ids

            articles.append(
                ArticleResponse(
                    id=UUID(article["id"]),
                    title=article["title"],
                    url=article["url"],
                    published_at=published_at,
                    tinkering_index=article["tinkering_index"],
                    ai_summary=article.get("ai_summary"),
                    feed_name=feed_info.get("name", "Unknown"),
                    category=feed_info.get("category", "Unknown"),
                    is_in_reading_list=is_in_reading_list,
                )
            )

        # 計算是否有下一頁
        has_next_page = (page * page_size) < total_count

        return paginated_response(
            items=articles, total_count=total_count, page=page, page_size=page_size
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve articles: {e!s}")
