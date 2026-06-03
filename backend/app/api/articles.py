"""
文章動態 API 模組

提供個人化文章動態查詢功能，基於使用者訂閱源。
"""

import asyncio
import time
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, cast

UTC = timezone.utc
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.auth import get_current_user
from app.schemas.article import ArticleResponse
from app.schemas.responses import (
    PaginatedResponse,
    SuccessResponse,
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
                "id, title, url, published_at, tinkering_index, ai_summary, actionable_takeaway, image_url, "
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

        # 3. 查詢用戶的 reading list 中的文章 IDs 和狀態
        reading_list_response = (
            supabase.client.table("reading_list")
            .select("article_id, status")
            .eq("user_id", str(current_user["user_id"]))
            .execute()
        )
        reading_list_status_map = {
            item["article_id"]: item["status"] for item in reading_list_response.data
        }

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
            is_in_reading_list = article["id"] in reading_list_status_map
            read_status = reading_list_status_map.get(article["id"])

            articles.append(
                ArticleResponse(
                    id=UUID(article["id"]),
                    title=article["title"],
                    url=article["url"],
                    published_at=published_at,
                    tinkering_index=article["tinkering_index"],
                    ai_summary=article.get("ai_summary"),
                    actionable_takeaway=article.get("actionable_takeaway"),
                    feed_name=feed_info.get("name", "Unknown"),
                    category=feed_info.get("category", "Unknown"),
                    is_in_reading_list=is_in_reading_list,
                    read_status=read_status,
                    image_url=article.get("image_url"),
                )
            )

        # 計算是否有下一頁
        has_next_page = (page * page_size) < total_count

        return paginated_response(
            items=articles, total_count=total_count, page=page, page_size=page_size
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve articles: {e!s}")


@router.get("/{article_id}", response_model=SuccessResponse[ArticleResponse])
async def get_article(
    article_id: UUID,
    current_user: dict = Depends(get_current_user),
):
    """
    查詢單一文章詳細資訊
    """
    try:
        supabase = SupabaseService()

        # 1. 查詢文章與 feed 資訊
        response = (
            supabase.client.table("articles")
            .select(
                "id, title, url, published_at, tinkering_index, ai_summary, actionable_takeaway, image_url, "
                "feeds!inner(name, category)"
            )
            .eq("id", str(article_id))
            .execute()
        )

        if not response.data:
            raise HTTPException(status_code=404, detail="Article not found")

        article = cast(Dict[str, Any], response.data[0])
        feed_info = cast(Dict[str, Any], article.get("feeds") or {})

        # 2. 檢查是否在 reading list 中
        reading_list_response = (
            supabase.client.table("reading_list")
            .select("status")
            .eq("user_id", str(current_user["user_id"]))
            .eq("article_id", str(article_id))
            .execute()
        )

        is_in_reading_list = len(reading_list_response.data) > 0
        read_status = reading_list_response.data[0]["status"] if is_in_reading_list else None

        # 處理 published_at
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

        result = ArticleResponse(
            id=UUID(str(article["id"])),
            title=str(article["title"]),
            url=article["url"],
            published_at=published_at,
            tinkering_index=article.get("tinkering_index") or 1,
            ai_summary=article.get("ai_summary"),
            actionable_takeaway=article.get("actionable_takeaway"),
            feed_name=feed_info.get("name", "Unknown"),
            category=feed_info.get("category", "Unknown"),
            is_in_reading_list=is_in_reading_list,
            read_status=read_status,
            image_url=article.get("image_url"),
        )

        return success_response(result)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve article: {e!s}")


# SWR (Stale-While-Revalidate) Memory Cache
# We initialize the cache for public recommended articles.
# It caches a pool of up to 10 high-quality recommended articles.
PUBLIC_RECOMMENDED_CACHE = {"data": [], "updated_at": 0.0, "is_updating": False}


async def _fetch_public_recommended_articles_pool() -> list:
    """
    從資料庫抓取並篩選公開推薦文章的池子（固定抓取最多 10 篇最高品質的文章）
    """
    try:
        supabase = SupabaseService()

        # 1. 單次查詢最新的 50 篇有 tinkering_index 評功能的文章作為池子
        # 排除掉 tinkering_index 為空的文章，其餘交由 Python 記憶體中做降級篩選
        response = (
            supabase.client.table("articles")
            .select(
                "id, title, url, published_at, tinkering_index, ai_summary, actionable_takeaway, "
                "feeds!inner(name, category)"
            )
            .not_.is_("tinkering_index", "null")
            .order("published_at", desc=True)
            .limit(50)
            .execute()
        )

        articles_data = response.data or []

        # 如果完全沒有有 tinkering_index 的文章，則放寬限制，抓取最原始的最新 50 篇文章
        if not articles_data:
            response_fallback = (
                supabase.client.table("articles")
                .select(
                    "id, title, url, published_at, tinkering_index, ai_summary, actionable_takeaway, "
                    "feeds!inner(name, category)"
                )
                .order("published_at", desc=True)
                .limit(50)
                .execute()
            )
            articles_data = response_fallback.data or []

        # 計算時間窗口（30 天內）- 使用 offset-aware datetime (UTC)
        thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)

        # 定義輔助時間轉換函式
        def parse_pub_at(art):
            if not art.get("published_at"):
                return None
            try:
                pub_at_str = str(art["published_at"])
                if pub_at_str.endswith("Z"):
                    pub_at_str = pub_at_str[:-1] + "+00:00"
                dt = datetime.fromisoformat(pub_at_str)
                # 確保為 offset-aware (UTC)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                return dt
            except:
                return None

        # 降級篩選步驟一：最近 30 天內且 tinkering_index >= 4 的高品質文章
        step1 = []
        for a in articles_data:
            dt = parse_pub_at(a)
            idx = a.get("tinkering_index")
            if dt and dt >= thirty_days_ago and idx is not None and idx >= 4:
                step1.append(a)

        # 降級篩選步驟二：如果不夠，加選最近 30 天內且 tinkering_index >= 3 的文章
        step2 = []
        if len(step1) < 10:
            step1_ids = {a["id"] for a in step1}
            for a in articles_data:
                if a["id"] in step1_ids:
                    continue
                dt = parse_pub_at(a)
                idx = a.get("tinkering_index")
                if dt and dt >= thirty_days_ago and idx is not None and idx >= 3:
                    step2.append(a)

        result_list = step1 + step2

        # 降級篩選步驟三：如果不夠，加選所有剩餘有評分的文章（不限時間）
        if len(result_list) < 10:
            result_ids = {a["id"] for a in result_list}
            step3 = []
            for a in articles_data:
                if a["id"] in result_ids:
                    continue
                if a.get("tinkering_index") is not None:
                    step3.append(a)
            result_list.extend(step3)

        # 降級篩選步驟四：如果仍不夠，補足任意最新文章
        if len(result_list) < 10:
            result_ids = {a["id"] for a in result_list}
            step4 = []
            for a in articles_data:
                if a["id"] in result_ids:
                    continue
                step4.append(a)
            result_list.extend(step4)

        # 固定快取最多 10 篇
        final_articles = result_list[:10]

        # 轉換格式為 ArticleResponse 相容格式
        articles = []
        for article in final_articles:
            feed_info = article.get("feeds", {})

            published_at = None
            if article.get("published_at"):
                try:
                    pub_at_str = str(article["published_at"])
                    if pub_at_str.endswith("Z"):
                        pub_at_str = pub_at_str[:-1] + "+00:00"
                    published_at = datetime.fromisoformat(pub_at_str)
                except (ValueError, TypeError):
                    published_at = None

            articles.append(
                {
                    "id": str(article["id"]),
                    "title": article["title"],
                    "url": article["url"],
                    "published_at": published_at.isoformat() if published_at else None,
                    "tinkering_index": article.get("tinkering_index", 0),
                    "ai_summary": article.get("ai_summary"),
                    "actionable_takeaway": article.get("actionable_takeaway"),
                    "feed_name": feed_info.get("name", "Unknown"),
                    "category": feed_info.get("category", "Unknown"),
                    "is_in_reading_list": False,
                    "read_status": None,
                }
            )
        return articles
    except Exception as e:
        print(f"Error in _fetch_public_recommended_articles_pool: {e}")
        return []


async def _async_refresh_public_articles():
    """
    非同步背景更新快取任務
    """
    try:
        new_data = await _fetch_public_recommended_articles_pool()
        if new_data:
            PUBLIC_RECOMMENDED_CACHE["data"] = new_data
            PUBLIC_RECOMMENDED_CACHE["updated_at"] = time.time()
    except Exception as e:
        print(f"Error in background cache refresh: {e}")
    finally:
        PUBLIC_RECOMMENDED_CACHE["is_updating"] = False


@router.get("/public/recommended")
async def get_public_recommended_articles(
    limit: int = Query(3, ge=1, le=10, description="數量（1-10）")
):
    """
    查詢公開推薦的文章（用於首頁展示）
    篩選標準：最近 30 天內且 tinkering_index 較高且最新發布的文章，不需使用者登入 (public)。
    導入 SWR (Stale-While-Revalidate) 本地記憶體快取，確保 sub-second 回應時間。
    """
    now = time.time()
    cache_age = now - PUBLIC_RECOMMENDED_CACHE["updated_at"]

    # 1. 記憶體中完全沒有資料 (Cold Start) -> 同步抓取並更新快取
    if not PUBLIC_RECOMMENDED_CACHE["data"]:
        PUBLIC_RECOMMENDED_CACHE["is_updating"] = True
        try:
            pool = await _fetch_public_recommended_articles_pool()
            PUBLIC_RECOMMENDED_CACHE["data"] = pool
            PUBLIC_RECOMMENDED_CACHE["updated_at"] = time.time()
        finally:
            PUBLIC_RECOMMENDED_CACHE["is_updating"] = False

        sliced_articles = PUBLIC_RECOMMENDED_CACHE["data"][:limit]
        return success_response(sliced_articles)

    # 2. 快取已過期 (大於 60 秒) 且目前沒有其他背景更新任務在進行中
    if cache_age >= 60.0 and not PUBLIC_RECOMMENDED_CACHE["is_updating"]:
        PUBLIC_RECOMMENDED_CACHE["is_updating"] = True
        # 觸發背景非同步更新任務，不阻塞當前請求
        asyncio.create_task(_async_refresh_public_articles())

    # 3. 立即回傳現有快取（可能是 stale 或者是未過期的快取），確保 0 延遲
    sliced_articles = PUBLIC_RECOMMENDED_CACHE["data"][:limit]
    return success_response(sliced_articles)
