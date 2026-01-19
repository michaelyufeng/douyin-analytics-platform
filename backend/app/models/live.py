"""
Live streaming database models.
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, BigInteger, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from app.db.database import Base


class Live(Base):
    """Live stream model."""
    __tablename__ = "lives"

    id = Column(Integer, primary_key=True, index=True)
    room_id = Column(String(50), unique=True, nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    title = Column(String(200))
    cover_url = Column(Text)
    stream_url = Column(Text)
    user_count = Column(Integer, default=0)
    total_user = Column(Integer, default=0)
    like_count = Column(BigInteger, default=0)
    status = Column(Integer, default=0)  # 0: offline, 1: live
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="lives")
    danmaku = relationship("LiveDanmaku", back_populates="live")


class LiveDanmaku(Base):
    """Live danmaku message model."""
    __tablename__ = "live_danmaku"

    id = Column(Integer, primary_key=True, index=True)
    live_id = Column(Integer, ForeignKey("lives.id"), index=True)
    user_nickname = Column(String(100))
    content = Column(Text)
    msg_type = Column(String(20))  # chat, gift, enter, like
    gift_name = Column(String(50))
    gift_count = Column(Integer)
    timestamp = Column(DateTime, default=datetime.utcnow)

    # Relationship
    live = relationship("Live", back_populates="danmaku")
