"""
Live streaming related business logic service.
"""
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from loguru import logger

from app.models.live import Live, LiveDanmaku
from app.core.crawler import DouyinCrawler


class LiveService:
    """Service for live streaming operations."""

    def __init__(self):
        self.crawler = DouyinCrawler()

    async def get_live_info(self, room_id: str, db: AsyncSession) -> Optional[dict]:
        """Get live room information."""
        try:
            data = await self.crawler.get_live_info(room_id)
            if data:
                # Save to database
                result = await db.execute(select(Live).where(Live.room_id == room_id))
                live = result.scalar_one_or_none()

                if live:
                    for key, value in data.items():
                        if hasattr(live, key):
                            setattr(live, key, value)
                else:
                    live = Live(**data)
                    db.add(live)
                await db.flush()

                return data
        except Exception as e:
            logger.error(f"Error fetching live info: {e}")

        return None

    async def get_live_by_user(self, sec_uid: str, db: AsyncSession) -> Optional[dict]:
        """Get live room by user sec_uid."""
        data = await self.crawler.get_live_by_user(sec_uid)
        return data

    async def get_live_danmaku(self, room_id: str, limit: int, db: AsyncSession) -> dict:
        """Get historical danmaku for a live room."""
        result = await db.execute(
            select(LiveDanmaku)
            .join(Live)
            .where(Live.room_id == room_id)
            .order_by(LiveDanmaku.timestamp.desc())
            .limit(limit)
        )
        danmaku = result.scalars().all()

        return {
            "room_id": room_id,
            "danmaku": [
                {
                    "user_nickname": d.user_nickname,
                    "content": d.content,
                    "msg_type": d.msg_type,
                    "gift_name": d.gift_name,
                    "gift_count": d.gift_count,
                    "timestamp": d.timestamp.isoformat()
                }
                for d in danmaku
            ],
            "total": len(danmaku)
        }

    async def get_live_ranking(self, count: int, db: AsyncSession) -> dict:
        """Get live room ranking."""
        data = await self.crawler.get_live_ranking(count)
        return data or {"lives": [], "total": 0}

    async def start_recording(self, room_id: str, db: AsyncSession) -> dict:
        """Start recording a live stream."""
        # This would start a background task to record the stream
        return {
            "status": "started",
            "room_id": room_id,
            "message": "Recording started"
        }
