"""
Task-related Pydantic schemas.
"""
from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import BaseModel, Field


class TaskBase(BaseModel):
    """Base task schema."""
    task_type: str = Field(..., pattern="^(user|video|live|keyword)$")
    target_id: str
    target_name: Optional[str] = None
    interval_seconds: int = Field(default=3600, ge=60)


class TaskConfig(BaseModel):
    """Task configuration."""
    notify_on_change: bool = False
    notify_threshold: Optional[float] = None
    save_snapshots: bool = True


class TaskCreate(TaskBase):
    """Task creation schema."""
    config: Optional[TaskConfig] = None


class TaskUpdate(BaseModel):
    """Task update schema."""
    target_name: Optional[str] = None
    interval_seconds: Optional[int] = Field(default=None, ge=60)
    is_active: Optional[bool] = None
    config: Optional[TaskConfig] = None


class TaskResponse(TaskBase):
    """Task response schema."""
    id: int
    is_active: bool
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    config: Optional[Dict[str, Any]] = None
    created_at: datetime

    class Config:
        from_attributes = True


class TaskListResponse(BaseModel):
    """Task list response."""
    tasks: List[TaskResponse]
    total: int
    skip: int
    limit: int


class TaskLog(BaseModel):
    """Task execution log."""
    task_id: int
    status: str
    message: str
    data: Optional[Dict[str, Any]] = None
    timestamp: datetime


class TaskLogResponse(BaseModel):
    """Task logs response."""
    task_id: int
    logs: List[TaskLog]
    total: int
