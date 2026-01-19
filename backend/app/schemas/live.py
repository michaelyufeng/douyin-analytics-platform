"""
Live streaming related Pydantic schemas.
"""
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel


class LiveBase(BaseModel):
    """Base live schema."""
    room_id: str
    title: Optional[str] = None
    cover_url: Optional[str] = None
    stream_url: Optional[str] = None


class LiveStats(BaseModel):
    """Live statistics."""
    user_count: int = 0
    total_user: int = 0
    like_count: int = 0


class LiveInfo(LiveBase, LiveStats):
    """Live info with all details."""
    user_id: Optional[int] = None
    status: int = 0
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None


class LiveResponse(LiveInfo):
    """Live response with metadata."""
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class LiveHost(BaseModel):
    """Live host info."""
    sec_uid: str
    nickname: str
    avatar_url: Optional[str] = None
    follower_count: int = 0


class LiveWithHost(LiveInfo):
    """Live with host info."""
    host: Optional[LiveHost] = None


class DanmakuMessage(BaseModel):
    """Danmaku message schema."""
    user_nickname: str
    content: str
    msg_type: str
    gift_name: Optional[str] = None
    gift_count: Optional[int] = None
    timestamp: datetime


class LiveDanmakuResponse(BaseModel):
    """Live danmaku response."""
    room_id: str
    danmaku: List[DanmakuMessage]
    total: int


class LiveRecordRequest(BaseModel):
    """Request to start live recording."""
    room_id: str


class LiveRecordResponse(BaseModel):
    """Response from live recording."""
    status: str
    room_id: str
    message: str
