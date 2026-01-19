"""
User database models.
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, BigInteger, Boolean, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from app.db.database import Base


class User(Base):
    """User model."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    sec_uid = Column(String(100), unique=True, nullable=False, index=True)
    uid = Column(String(50), index=True)
    nickname = Column(String(100))
    unique_id = Column(String(100))
    signature = Column(Text)
    avatar_url = Column(Text)
    follower_count = Column(BigInteger, default=0)
    following_count = Column(BigInteger, default=0)
    total_favorited = Column(BigInteger, default=0)
    aweme_count = Column(Integer, default=0)
    is_verified = Column(Boolean, default=False)
    verify_info = Column(Text)
    region = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    videos = relationship("Video", back_populates="user")
    comments = relationship("Comment", back_populates="user")
    lives = relationship("Live", back_populates="user")
    snapshots = relationship("UserSnapshot", back_populates="user")


class UserSnapshot(Base):
    """User snapshot for tracking changes over time."""
    __tablename__ = "user_snapshots"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    follower_count = Column(BigInteger)
    following_count = Column(BigInteger)
    total_favorited = Column(BigInteger)
    aweme_count = Column(Integer)
    snapshot_time = Column(DateTime, default=datetime.utcnow)

    # Relationship
    user = relationship("User", back_populates="snapshots")
