"""
Video database models.
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, BigInteger, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from app.db.database import Base


class Video(Base):
    """Video model."""
    __tablename__ = "videos"

    id = Column(Integer, primary_key=True, index=True)
    aweme_id = Column(String(50), unique=True, nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    desc = Column(Text)
    video_url = Column(Text)
    cover_url = Column(Text)
    music_url = Column(Text)
    duration = Column(Integer)
    play_count = Column(BigInteger, default=0)
    digg_count = Column(BigInteger, default=0)
    comment_count = Column(BigInteger, default=0)
    share_count = Column(BigInteger, default=0)
    collect_count = Column(BigInteger, default=0)
    create_time = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="videos")
    comments = relationship("Comment", back_populates="video")
    snapshots = relationship("VideoSnapshot", back_populates="video")


class VideoSnapshot(Base):
    """Video snapshot for tracking changes over time."""
    __tablename__ = "video_snapshots"

    id = Column(Integer, primary_key=True, index=True)
    video_id = Column(Integer, ForeignKey("videos.id"), nullable=False, index=True)
    play_count = Column(BigInteger)
    digg_count = Column(BigInteger)
    comment_count = Column(BigInteger)
    share_count = Column(BigInteger)
    collect_count = Column(BigInteger)
    snapshot_time = Column(DateTime, default=datetime.utcnow)

    # Relationship
    video = relationship("Video", back_populates="snapshots")
