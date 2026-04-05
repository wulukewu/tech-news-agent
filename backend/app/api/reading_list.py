"""
Reading List API Module

Provides reading list management endpoints for web frontend.
Implements POST /api/reading-list, GET /api/reading-list, and DELETE /api/reading-list/{article_id}.

Validates: Requirements 1.1, 1.3, 1.6, 6.1, 6.7, 13.1, 13.2, 13.3
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional
from uuid import UUID

from app.api.auth import get_current_user
from app.services.supabase_service import SupabaseService
from app.core.exceptions import SupabaseServiceError
from app.schemas.reading_list import (
    AddToReadingListRequest,
    ReadingListResponse,
    ReadingListItemResponse,
    MessageResponse
)

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/reading-list", response_model=MessageResponse)
async def add_to_reading_list(
    request: AddToReadingListRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    加入文章到閱讀清單
    
    使用 UPSERT 確保冪等性：重複加入相同文章不會產生錯誤。
    
    Args:
        request: 包含 article_id 的請求
        current_user: 當前使用者資訊（從 JWT token 提取）
    
    Returns:
        MessageResponse: 成功訊息
    
    Raises:
        HTTPException: 400 當 article_id 無效時
        HTTPException: 404 當文章不存在時
        HTTPException: 500 當資料庫操作失敗時
    
    Validates: Requirements 1.1, 6.1, 6.7, 13.1
    """
    try:
        supabase = SupabaseService()
        discord_id = current_user["discord_id"]
        article_id = request.article_id
        
        logger.info(
            f"Adding article to reading list",
            extra={
                "discord_id": discord_id,
                "article_id": str(article_id)
            }
        )
        
        # 先驗證文章是否存在
        article_check = supabase.client.table('articles')\
            .select('id')\
            .eq('id', str(article_id))\
            .execute()
        
        if not article_check.data or len(article_check.data) == 0:
            raise HTTPException(
                status_code=404,
                detail=f"Article not found: {article_id}"
            )
        
        # 加入閱讀清單（使用 UPSERT）
        await supabase.save_to_reading_list(discord_id, article_id)
        
        logger.info(
            f"Successfully added article to reading list",
            extra={
                "discord_id": discord_id,
                "article_id": str(article_id)
            }
        )
        
        return MessageResponse(
            message="Article added to reading list",
            article_id=article_id
        )
        
    except HTTPException:
        # 重新拋出 HTTP 例外
        raise
    except ValueError as e:
        # 驗證錯誤（無效的 UUID 格式）
        logger.warning(
            f"Invalid article_id format: {e}",
            extra={"article_id": str(request.article_id)}
        )
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    except SupabaseServiceError as e:
        # 資料庫錯誤
        logger.error(
            f"Database error adding to reading list: {e}",
            exc_info=True,
            extra={
                "discord_id": current_user.get("discord_id"),
                "article_id": str(request.article_id)
            }
        )
        raise HTTPException(
            status_code=500,
            detail="Failed to add article to reading list"
        )
    except Exception as e:
        # 未預期的錯誤
        logger.error(
            f"Unexpected error adding to reading list: {e}",
            exc_info=True,
            extra={
                "discord_id": current_user.get("discord_id"),
                "article_id": str(request.article_id)
            }
        )
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred"
        )


@router.get("/reading-list", response_model=ReadingListResponse)
async def get_reading_list(
    page: int = Query(1, ge=1, description="頁碼（從 1 開始）"),
    page_size: int = Query(20, ge=1, le=100, description="每頁項目數（1-100）"),
    status: Optional[str] = Query(None, description="狀態篩選（Unread, Read, Archived）"),
    current_user: dict = Depends(get_current_user)
):
    """
    查詢閱讀清單
    
    支援狀態篩選和分頁。結果按 added_at 降序排列（最新加入的在最前面）。
    
    Args:
        page: 頁碼（從 1 開始）
        page_size: 每頁項目數（1-100）
        status: 可選的狀態篩選（Unread, Read, Archived）
        current_user: 當前使用者資訊（從 JWT token 提取）
    
    Returns:
        ReadingListResponse: 包含閱讀清單項目和分頁資訊
    
    Raises:
        HTTPException: 400 當狀態值無效時
        HTTPException: 500 當資料庫查詢失敗時
    
    Validates: Requirements 1.3, 1.4, 1.7, 6.1, 13.2
    """
    try:
        supabase = SupabaseService()
        discord_id = current_user["discord_id"]
        
        logger.info(
            f"Fetching reading list",
            extra={
                "discord_id": discord_id,
                "page": page,
                "page_size": page_size,
                "status": status
            }
        )
        
        # 驗證狀態值（如果提供）
        if status:
            allowed_statuses = {'Unread', 'Read', 'Archived'}
            if status not in allowed_statuses:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid status: '{status}'. Allowed values are: {', '.join(sorted(allowed_statuses))}"
                )
        
        # 取得使用者 UUID
        user_uuid = await supabase.get_or_create_user(discord_id)
        
        # 建立基礎查詢
        query = supabase.client.table('reading_list')\
            .select(
                'article_id, status, rating, added_at, updated_at, '
                'articles!inner(id, title, url, feeds!inner(category))',
                count='exact'
            )\
            .eq('user_id', str(user_uuid))
        
        # 加入狀態篩選（如果提供）
        if status:
            query = query.eq('status', status)
        
        # 計算分頁
        offset = (page - 1) * page_size
        
        # 執行查詢
        response = query\
            .order('added_at', desc=True)\
            .range(offset, offset + page_size - 1)\
            .execute()
        
        # 取得總數
        total_count = response.count if response.count else 0
        
        # 轉換為回應格式
        items = []
        for item_data in response.data:
            try:
                # 從 JOIN 結果中提取文章資訊
                article_data = item_data.get('articles')
                if not article_data:
                    logger.warning(f"Article data missing for reading list item: {item_data}")
                    continue
                
                # 從 nested JOIN 結果中提取 feed 資訊
                feed_data = article_data.get('feeds')
                if not feed_data:
                    logger.warning(f"Feed data missing for article: {article_data}")
                    continue
                
                items.append(
                    ReadingListItemResponse(
                        article_id=UUID(item_data['article_id']),
                        title=article_data['title'],
                        url=article_data['url'],
                        category=feed_data['category'],
                        status=item_data['status'],
                        rating=item_data.get('rating'),
                        added_at=item_data['added_at'],
                        updated_at=item_data['updated_at']
                    )
                )
            except Exception as e:
                logger.warning(
                    f"Failed to parse reading list item: {e}",
                    extra={"item_data": item_data}
                )
                continue
        
        # 計算是否有下一頁
        has_next_page = (page * page_size) < total_count
        
        logger.info(
            f"Successfully fetched reading list",
            extra={
                "discord_id": discord_id,
                "items_count": len(items),
                "total_count": total_count,
                "page": page
            }
        )
        
        return ReadingListResponse(
            items=items,
            page=page,
            page_size=page_size,
            total_count=total_count,
            has_next_page=has_next_page
        )
        
    except HTTPException:
        # 重新拋出 HTTP 例外
        raise
    except ValueError as e:
        # 驗證錯誤
        logger.warning(
            f"Validation error: {e}",
            extra={"status": status}
        )
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    except SupabaseServiceError as e:
        # 資料庫錯誤
        logger.error(
            f"Database error fetching reading list: {e}",
            exc_info=True,
            extra={
                "discord_id": current_user.get("discord_id"),
                "page": page,
                "status": status
            }
        )
        raise HTTPException(
            status_code=500,
            detail="Failed to fetch reading list"
        )
    except Exception as e:
        # 未預期的錯誤
        logger.error(
            f"Unexpected error fetching reading list: {e}",
            exc_info=True,
            extra={
                "discord_id": current_user.get("discord_id"),
                "page": page,
                "status": status
            }
        )
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred"
        )


@router.delete("/reading-list/{article_id}", response_model=MessageResponse)
async def remove_from_reading_list(
    article_id: UUID,
    current_user: dict = Depends(get_current_user)
):
    """
    從閱讀清單移除文章
    
    Args:
        article_id: 文章 UUID
        current_user: 當前使用者資訊（從 JWT token 提取）
    
    Returns:
        MessageResponse: 成功訊息
    
    Raises:
        HTTPException: 404 當閱讀清單項目不存在時
        HTTPException: 500 當資料庫操作失敗時
    
    Validates: Requirements 1.6, 6.6, 13.3
    """
    try:
        supabase = SupabaseService()
        discord_id = current_user["discord_id"]
        
        logger.info(
            f"Removing article from reading list",
            extra={
                "discord_id": discord_id,
                "article_id": str(article_id)
            }
        )
        
        # 取得使用者 UUID
        user_uuid = await supabase.get_or_create_user(discord_id)
        
        # 刪除閱讀清單項目
        response = supabase.client.table('reading_list')\
            .delete()\
            .eq('user_id', str(user_uuid))\
            .eq('article_id', str(article_id))\
            .execute()
        
        if not response.data or len(response.data) == 0:
            raise HTTPException(
                status_code=404,
                detail=f"Reading list entry not found for article: {article_id}"
            )
        
        logger.info(
            f"Successfully removed article from reading list",
            extra={
                "discord_id": discord_id,
                "article_id": str(article_id)
            }
        )
        
        return MessageResponse(
            message="Article removed from reading list",
            article_id=article_id
        )
        
    except HTTPException:
        # 重新拋出 HTTP 例外
        raise
    except ValueError as e:
        # 驗證錯誤（無效的 UUID 格式）
        logger.warning(
            f"Invalid article_id format: {e}",
            extra={"article_id": str(article_id)}
        )
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    except SupabaseServiceError as e:
        # 資料庫錯誤
        logger.error(
            f"Database error removing from reading list: {e}",
            exc_info=True,
            extra={
                "discord_id": current_user.get("discord_id"),
                "article_id": str(article_id)
            }
        )
        raise HTTPException(
            status_code=500,
            detail="Failed to remove article from reading list"
        )
    except Exception as e:
        # 未預期的錯誤
        logger.error(
            f"Unexpected error removing from reading list: {e}",
            exc_info=True,
            extra={
                "discord_id": current_user.get("discord_id"),
                "article_id": str(article_id)
            }
        )
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred"
        )
