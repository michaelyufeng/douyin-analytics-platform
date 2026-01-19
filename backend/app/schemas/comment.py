"""
Comment-related Pydantic schemas.
"""
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel


class CommentBase(BaseModel):
    """Base comment schema."""
    cid: str
    content: str
    digg_count: int = 0
    reply_count: int = 0


class CommentUser(BaseModel):
    """Comment user info."""
    uid: str
    nickname: str
    avatar_url: Optional[str] = None


class CommentDetail(CommentBase):
    """Comment with all details."""
    user: Optional[CommentUser] = None
    reply_to_cid: Optional[str] = None
    ip_label: Optional[str] = None
    create_time: Optional[datetime] = None


class CommentResponse(CommentDetail):
    """Comment response with metadata."""
    id: int
    video_id: int
    user_id: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True


class CommentListResponse(BaseModel):
    """Paginated comment list response."""
    comments: List[CommentDetail]
    cursor: int
    has_more: bool
    total: int
