from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_serializer


class RSSSource(BaseModel):
    id: UUID
    name: str
    url: HttpUrl
    category: str


class AIAnalysis(BaseModel):
    is_hardcore: bool = Field(description="Whether the article is recommended or discarded")
    reason: str = Field(
        description="A one-sentence explanation of why it was recommended or discarded"
    )
    actionable_takeaway: Optional[str] = Field(
        default="", description="The actionable value extracted (can be empty if discarded)"
    )
    tinkering_index: int = Field(
        ge=1, le=5, description="Tinkering index (1-5) indicating technical complexity"
    )


class ArticleSchema(BaseModel):
    """文章資料模型（更新以匹配 Supabase 結構）"""

    # 基本資訊
    id: Optional[UUID] = None  # 新增：文章 UUID（從資料庫查詢時使用）
    title: str = Field(..., max_length=2000)
    url: HttpUrl

    # 來源資訊（重新命名）
    feed_id: UUID  # 新增：關聯到 feeds 表
    feed_name: str  # 重新命名自 source_name
    category: str  # 重新命名自 source_category

    # 時間資訊
    published_at: Optional[datetime] = None  # 新增：文章發布時間
    created_at: datetime = Field(default_factory=datetime.utcnow)  # 新增：系統建立時間

    # AI 分析結果
    tinkering_index: Optional[int] = Field(None, ge=1, le=5)  # 移至頂層
    ai_summary: Optional[str] = Field(None, max_length=5000)  # 新增：AI 摘要
    ai_analysis: Optional[AIAnalysis] = None  # 保留：完整 AI 分析

    # 向量嵌入
    embedding: Optional[list[float]] = None  # 新增：用於語義搜尋

    # 移除的欄位：
    # - content_preview: 不再需要，使用 ai_summary 替代
    # - raw_data: 不再需要，資料庫結構化儲存


class ArticlePageResult(BaseModel):
    page_id: str
    page_url: str
    title: str
    category: str
    tinkering_index: int


class ReadingListItem(BaseModel):
    article_id: UUID  # 文章 UUID（更新自 page_id）
    title: str  # 文章標題
    url: HttpUrl  # 文章 URL
    category: str  # 分類（重新命名自 source_category）
    status: str  # 閱讀狀態（Unread, Read, Archived）
    rating: Optional[int] = None  # 評分（1–5，未評分為 None）
    added_at: datetime  # 新增時間
    updated_at: datetime  # 更新時間


class BatchResult(BaseModel):
    """批次操作結果"""

    inserted_count: int = Field(description="成功插入的記錄數")
    updated_count: int = Field(description="成功更新的記錄數")
    failed_count: int = Field(description="失敗的記錄數")
    failed_articles: list[dict] = Field(default_factory=list, description="失敗的文章資訊（包含錯誤原因）")

    @property
    def total_processed(self) -> int:
        """總處理數量"""
        return self.inserted_count + self.updated_count + self.failed_count

    @property
    def success_rate(self) -> float:
        """成功率（0-1）"""
        if self.total_processed == 0:
            return 1.0
        return (self.inserted_count + self.updated_count) / self.total_processed


class Subscription(BaseModel):
    """使用者訂閱資訊"""

    feed_id: UUID
    name: str
    url: HttpUrl
    category: str
    subscribed_at: datetime


class ArticleResponse(BaseModel):
    """文章回應（用於 API）"""

    id: UUID = Field(..., description="文章 UUID")
    title: str = Field(..., description="文章標題")
    url: HttpUrl = Field(..., description="文章 URL")
    published_at: Optional[datetime] = Field(
        None, description="發布時間", serialization_alias="publishedAt"
    )
    tinkering_index: int = Field(
        ..., ge=1, le=5, description="技術複雜度（1-5）", serialization_alias="tinkeringIndex"
    )
    ai_summary: Optional[str] = Field(None, description="AI 摘要", serialization_alias="aiSummary")
    feed_name: str = Field(..., description="來源名稱", serialization_alias="feedName")
    category: str = Field(..., description="分類")
    is_in_reading_list: bool = Field(
        False, description="是否已加入閱讀清單", serialization_alias="isInReadingList"
    )

    model_config = ConfigDict(populate_by_name=True, by_alias=True)

    @field_serializer("published_at")
    def serialize_published_at(self, value: Optional[datetime], _info) -> Optional[str]:
        """確保 published_at 序列化為 ISO 8601 格式"""
        return value.isoformat() if value else None


class ArticleListResponse(BaseModel):
    """文章列表回應（含分頁）"""

    articles: list[ArticleResponse] = Field(..., description="文章列表")
    page: int = Field(..., ge=1, description="當前頁碼")
    page_size: int = Field(..., ge=1, le=100, description="每頁文章數", serialization_alias="pageSize")
    total_count: int = Field(..., ge=0, description="總文章數", serialization_alias="totalCount")
    has_next_page: bool = Field(..., description="是否有下一頁", serialization_alias="hasNextPage")

    model_config = ConfigDict(populate_by_name=True, by_alias=True)
