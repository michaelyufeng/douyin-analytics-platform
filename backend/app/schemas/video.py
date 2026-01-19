"""
Video-related Pydantic schemas.
"""
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field, HttpUrl


class VideoBase(BaseModel):
    """Base video schema."""
    aweme_id: str
    desc: Optional[str] = None
    video_url: Optional[str] = None
    cover_url: Optional[str] = None
    music_url: Optional[str] = None
    duration: Optional[int] = None


class VideoStats(BaseModel):
    """Video statistics."""
    play_count: int = 0
    digg_count: int = 0
    comment_count: int = 0
    share_count: int = 0
    collect_count: int = 0


class VideoDetail(VideoBase, VideoStats):
    """Video detail with all info."""
    user_id: Optional[int] = None
    create_time: Optional[datetime] = None


class VideoResponse(VideoDetail):
    """Video response with metadata."""
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class VideoSnapshot(BaseModel):
    """Video snapshot for historical data."""
    play_count: int
    digg_count: int
    comment_count: int
    share_count: int
    collect_count: int
    snapshot_time: datetime


class VideoParseRequest(BaseModel):
    """Request for video URL parsing."""
    url: str = Field(..., min_length=10)


class VideoParseResponse(BaseModel):
    """Response from video URL parsing."""
    aweme_id: str
    video_url: str
    cover_url: str
    desc: str
    author: dict


class VideoDownloadRequest(BaseModel):
    """Request for video download."""
    aweme_id: str
    quality: str = Field(default="high", pattern="^(high|medium|low)$")


class VideoDownloadResponse(BaseModel):
    """Response from video download."""
    status: str
    file_path: Optional[str] = None
    message: str
