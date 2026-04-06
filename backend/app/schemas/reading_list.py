"""
Reading List API Schemas

Pydantic schemas for reading list API requests and responses.
"""

from pydantic import BaseModel, Field, HttpUrl, validator
from typing import Optional, List
from datetime import datetime
from uuid import UUID


class AddToReadingListRequest(BaseModel):
    """加入文章到閱讀清單請求"""
    article_id: UUID = Field(..., description="文章 UUID")


class UpdateRatingRequest(BaseModel):
    """更新評分請求"""
    rating: Optional[int] = Field(None, ge=1, le=5, description="評分（1-5）或 null 清除評分")

    @validator('rating')
    def validate_rating(cls, v):
        if v is None:
            return v  # Allow null to clear rating
        if not isinstance(v, int):
            raise ValueError("Rating must be an integer or null")
        if not (1 <= v <= 5):
            raise ValueError("Rating must be between 1 and 5")
        return v


class UpdateStatusRequest(BaseModel):
    """更新閱讀狀態請求"""
    status: str = Field(..., description="閱讀狀態")

    @validator('status')
    def validate_status(cls, v):
        allowed = {'Unread', 'Read', 'Archived'}
        if v not in allowed:
            raise ValueError(f"Status must be one of {', '.join(sorted(allowed))}")
        return v


class ReadingListItemResponse(BaseModel):
    """閱讀清單項目回應"""
    article_id: UUID = Field(..., description="文章 UUID", alias="articleId")
    title: str = Field(..., description="文章標題")
    url: HttpUrl = Field(..., description="文章 URL")
    category: str = Field(..., description="分類")
    status: str = Field(..., description="閱讀狀態")
    rating: Optional[int] = Field(None, description="評分（1-5）")
    added_at: datetime = Field(..., description="加入時間", alias="addedAt")
    updated_at: datetime = Field(..., description="更新時間", alias="updatedAt")
    
    class Config:
        populate_by_name = True


class ReadingListResponse(BaseModel):
    """閱讀清單回應（含分頁）"""
    items: List[ReadingListItemResponse] = Field(..., description="閱讀清單項目")
    page: int = Field(..., ge=1, description="當前頁碼")
    page_size: int = Field(..., ge=1, le=100, description="每頁項目數", alias="pageSize")
    total_count: int = Field(..., ge=0, description="總項目數", alias="totalCount")
    has_next_page: bool = Field(..., description="是否有下一頁", alias="hasNextPage")
    
    class Config:
        populate_by_name = True


class MessageResponse(BaseModel):
    """通用訊息回應"""
    message: str = Field(..., description="回應訊息")
    article_id: Optional[UUID] = Field(None, description="文章 UUID", alias="articleId")
    rating: Optional[int] = Field(None, description="評分")
    status: Optional[str] = Field(None, description="狀態")
    
    class Config:
        populate_by_name = True
