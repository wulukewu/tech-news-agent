"""
文章動態 API 模組

提供個人化文章動態查詢功能，基於使用者訂閱源。
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List
from datetime import datetime, timedelta
from uuid import UUID

from app.api.auth import get_current_user
from app.services.supabase_service import SupabaseService
from app.schemas.article import ArticleResponse, ArticleListResponse

router = APIRouter()


@router.get("/categories")
async def get_categories(
    current_user: dict = Depends(get_current_user)
):
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
        response = (
            supabase.client.table("feeds")
            .select("category")
            .eq("is_active", True)
            .execute()
        )

        # 提取不重複的類別
        categories = list(set(feed["category"] for feed in response.data if feed.get("category")))
        categories.sort()

        return {"categories": categories}

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve categories: {str(e)}"
        )


@router.get("/me", response_model=ArticleListResponse)
async def get_my_articles(
    page: int = Query(1, ge=1, description="頁碼（從 1 開始）"),
    page_size: int = Query(20, ge=1, le=100, description="每頁文章數（1-100）"),
    categories: str = Query(None, description="篩選類別（逗號分隔，例如：前端開發,AI 應用）"),
    current_user: dict = Depends(get_current_user)
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
            return ArticleListResponse(
                articles=[],
                page=page,
                page_size=page_size,
                total_count=0,
                has_next_page=False
            )

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
            query
            .order("tinkering_index", desc=True)
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

        # 組合回應
        articles = []
        for article in response.data:
            feed_info = article.get("feeds", {})
            articles.append(
                ArticleResponse(
                    id=UUID(article["id"]),
                    title=article["title"],
                    url=article["url"],
                    published_at=datetime.fromisoformat(article["published_at"]) if article.get("published_at") else None,
                    tinkering_index=article["tinkering_index"],
                    ai_summary=article.get("ai_summary"),
                    feed_name=feed_info.get("name", "Unknown"),
                    category=feed_info.get("category", "Unknown")
                )
            )

        # 計算是否有下一頁
        has_next_page = (page * page_size) < total_count

        return ArticleListResponse(
            articles=articles,
            page=page,
            page_size=page_size,
            total_count=total_count,
            has_next_page=has_next_page
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve articles: {str(e)}"
        )
