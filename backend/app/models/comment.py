"""
Comment database models.
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from app.db.database import Base


class Comment(Base):
    """Comment model."""
    __tablename__ = "comments"

    id = Column(Integer, primary_key=True, index=True)
    cid = Column(String(50), unique=True, nullable=False, index=True)
    video_id = Column(Integer, ForeignKey("videos.id"), index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    content = Column(Text)
    digg_count = Column(Integer, default=0)
    reply_count = Column(Integer, default=0)
    reply_to_cid = Column(String(50), index=True)
    ip_label = Column(String(50))
    create_time = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    video = relationship("Video", back_populates="comments")
    user = relationship("User", back_populates="comments")
