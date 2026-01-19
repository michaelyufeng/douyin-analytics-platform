"""
Task and analysis database models.
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, Text, DateTime, JSON

from app.db.database import Base


class MonitorTask(Base):
    """Monitor task model."""
    __tablename__ = "monitor_tasks"

    id = Column(Integer, primary_key=True, index=True)
    task_type = Column(String(20), nullable=False, index=True)  # user, video, live, keyword
    target_id = Column(String(100), nullable=False, index=True)
    target_name = Column(String(100))
    interval_seconds = Column(Integer, default=3600)
    is_active = Column(Boolean, default=True)
    last_run = Column(DateTime)
    next_run = Column(DateTime)
    config = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)


class AnalysisResult(Base):
    """Analysis result model."""
    __tablename__ = "analysis_results"

    id = Column(Integer, primary_key=True, index=True)
    analysis_type = Column(String(50), index=True)  # user, video, comments, trends
    target_type = Column(String(20))
    target_id = Column(String(100), index=True)
    result = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)


class TaskLog(Base):
    """Task execution log model."""
    __tablename__ = "task_logs"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, index=True)
    status = Column(String(20))  # success, failed, running
    message = Column(Text)
    data = Column(JSON)
    timestamp = Column(DateTime, default=datetime.utcnow)
