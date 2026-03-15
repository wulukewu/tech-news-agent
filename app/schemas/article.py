from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, List, Dict, Any
from datetime import datetime

class RSSSource(BaseModel):
    name: str
    url: HttpUrl
    category: str

class AIAnalysis(BaseModel):
    is_hardcore: bool = Field(description="Whether the article is recommended or discarded")
    reason: str = Field(description="A one-sentence explanation of why it was recommended or discarded")
    actionable_takeaway: Optional[str] = Field(default="", description="The actionable value extracted (can be empty if discarded)")
    tinkering_index: int = Field(ge=0, le=5, description="Difficulty of deployment or setup (1-5)")

class ArticleSchema(BaseModel):
    title: str
    url: str
    content_preview: str # A short preview of the content (first 800 chars)
    published_date: Optional[datetime] = None
    
    # Metadata from Notion source
    source_category: str
    source_name: str
    
    # AI Analysis results
    ai_analysis: Optional[AIAnalysis] = None
    
    # Raw data for fallback
    raw_data: Optional[Dict[str, Any]] = None
