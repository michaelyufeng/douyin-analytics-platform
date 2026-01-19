"""
User-related Pydantic schemas.
"""
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field


class UserBase(BaseModel):
    """Base user schema."""
    sec_uid: str
    uid: Optional[str] = None
    nickname: Optional[str] = None
    unique_id: Optional[str] = None
    signature: Optional[str] = None
    avatar_url: Optional[str] = None


class UserProfile(UserBase):
    """User profile with stats."""
    follower_count: int = 0
    following_count: int = 0
    total_favorited: int = 0
    aweme_count: int = 0
    is_verified: bool = False
    verify_info: Optional[str] = None
    region: Optional[str] = None


class UserResponse(UserProfile):
    """User response with metadata."""
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UserSnapshot(BaseModel):
    """User snapshot for historical data."""
    follower_count: int
    following_count: int
    total_favorited: int
    aweme_count: int
    snapshot_time: datetime


class UserHistory(BaseModel):
    """User history response."""
    user_id: int
    snapshots: List[UserSnapshot]


class UserCompareRequest(BaseModel):
    """Request for user comparison."""
    sec_uids: List[str] = Field(..., min_length=2, max_length=10)


class BatchUserRequest(BaseModel):
    """Request for batch user retrieval."""
    sec_uids: List[str] = Field(..., min_length=1, max_length=50)


class UserCompareResult(BaseModel):
    """User comparison result."""
    users: List[UserProfile]
    comparison: dict
