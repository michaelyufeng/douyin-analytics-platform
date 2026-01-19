"""
Analysis-related Pydantic schemas.
"""
from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import BaseModel, Field


class UserAnalysisRequest(BaseModel):
    """User analysis request."""
    sec_uid: str


class VideoAnalysisRequest(BaseModel):
    """Video analysis request."""
    aweme_id: str


class CommentAnalysisRequest(BaseModel):
    """Comment analysis request."""
    aweme_id: str


class TrendAnalysisRequest(BaseModel):
    """Trend analysis request."""
    keyword: str
    days: int = Field(default=7, ge=1, le=30)


class SentimentResult(BaseModel):
    """Sentiment analysis result."""
    positive: float
    negative: float
    neutral: float


class UserAnalysisResult(BaseModel):
    """User analysis result."""
    sec_uid: str
    nickname: str
    engagement_rate: float
    avg_views: float
    avg_likes: float
    posting_frequency: float  # posts per week
    best_posting_time: Optional[str] = None
    content_categories: List[str]
    growth_trend: str  # "growing", "stable", "declining"
    top_videos: List[Dict[str, Any]]


class VideoAnalysisResult(BaseModel):
    """Video analysis result."""
    aweme_id: str
    engagement_rate: float
    viral_score: float
    best_engagement_time: Optional[str] = None
    audience_sentiment: SentimentResult
    similar_videos: List[Dict[str, Any]]


class CommentAnalysisResult(BaseModel):
    """Comment analysis result."""
    aweme_id: str
    total_comments: int
    sentiment: SentimentResult
    top_keywords: List[Dict[str, Any]]
    user_demographics: Dict[str, Any]


class TrendAnalysisResult(BaseModel):
    """Trend analysis result."""
    keyword: str
    trend_direction: str  # "rising", "stable", "falling"
    search_volume: List[Dict[str, Any]]
    related_topics: List[str]
    top_creators: List[Dict[str, Any]]


class AnalysisReport(BaseModel):
    """Analysis report."""
    id: int
    analysis_type: str
    target_type: str
    target_id: str
    result: Dict[str, Any]
    created_at: datetime

    class Config:
        from_attributes = True
