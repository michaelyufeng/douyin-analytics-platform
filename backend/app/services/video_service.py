"""
Video-related business logic service.
"""
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from loguru import logger

from app.models.video import Video, VideoSnapshot
from app.core.crawler import DouyinCrawler


class VideoService:
    """Service for video-related operations."""

    def __init__(self):
        self.crawler = DouyinCrawler()

    async def get_video_detail(self, aweme_id: str, db: AsyncSession) -> Optional[dict]:
        """Get video detail from Douyin API."""
        # Try to get from database first
        result = await db.execute(select(Video).where(Video.aweme_id == aweme_id))
        video = result.scalar_one_or_none()

        # Fetch fresh data from API
        try:
            video_data = await self.crawler.get_video_detail(aweme_id)
            if video_data:
                if video:
                    # Update existing video
                    for key, value in video_data.items():
                        if hasattr(video, key):
                            setattr(video, key, value)
                else:
                    # Create new video
                    video = Video(**video_data)
                    db.add(video)
                await db.flush()
                await db.refresh(video)

                # Create snapshot
                snapshot = VideoSnapshot(
                    video_id=video.id,
                    play_count=video.play_count,
                    digg_count=video.digg_count,
                    comment_count=video.comment_count,
                    share_count=video.share_count,
                    collect_count=video.collect_count
                )
                db.add(snapshot)
        except Exception as e:
            logger.error(f"Error fetching video detail: {e}")
            if not video:
                return None

        return {
            "id": video.id,
            "aweme_id": video.aweme_id,
            "desc": video.desc,
            "video_url": video.video_url,
            "cover_url": video.cover_url,
            "music_url": video.music_url,
            "duration": video.duration,
            "play_count": video.play_count,
            "digg_count": video.digg_count,
            "comment_count": video.comment_count,
            "share_count": video.share_count,
            "collect_count": video.collect_count,
            "create_time": video.create_time,
            "created_at": video.created_at,
            "updated_at": video.updated_at
        }

    async def get_video_comments(self, aweme_id: str, cursor: int, count: int, db: AsyncSession) -> dict:
        """Get video comments."""
        data = await self.crawler.get_video_comments(aweme_id, cursor, count)
        return data or {"comments": [], "cursor": 0, "has_more": False}

    async def get_comment_replies(self, comment_id: str, cursor: int, count: int, db: AsyncSession) -> dict:
        """Get comment replies."""
        data = await self.crawler.get_comment_replies(comment_id, cursor, count)
        return data or {"replies": [], "cursor": 0, "has_more": False}

    async def get_related_videos(self, aweme_id: str, count: int, db: AsyncSession) -> dict:
        """Get related videos."""
        data = await self.crawler.get_related_videos(aweme_id, count)
        return data or {"videos": []}

    async def get_mix_videos(self, mix_id: str, cursor: int, count: int, db: AsyncSession) -> dict:
        """Get videos from a mix/collection."""
        data = await self.crawler.get_mix_videos(mix_id, cursor, count)
        return data or {"videos": [], "cursor": 0, "has_more": False}

    async def get_video_history(self, video_id: int, days: int, db: AsyncSession) -> dict:
        """Get video stats history."""
        from datetime import datetime, timedelta
        from sqlalchemy import and_

        start_date = datetime.utcnow() - timedelta(days=days)
        result = await db.execute(
            select(VideoSnapshot)
            .where(
                and_(
                    VideoSnapshot.video_id == video_id,
                    VideoSnapshot.snapshot_time >= start_date
                )
            )
            .order_by(VideoSnapshot.snapshot_time)
        )
        snapshots = result.scalars().all()

        return {
            "video_id": video_id,
            "snapshots": [
                {
                    "play_count": s.play_count,
                    "digg_count": s.digg_count,
                    "comment_count": s.comment_count,
                    "share_count": s.share_count,
                    "collect_count": s.collect_count,
                    "snapshot_time": s.snapshot_time.isoformat()
                }
                for s in snapshots
            ]
        }

    async def parse_video_url(self, url: str, db: AsyncSession) -> dict:
        """Parse video URL to extract video info."""
        data = await self.crawler.parse_video_url(url)
        return data or {"error": "Failed to parse URL"}

    async def download_video(self, aweme_id: str, quality: str, db: AsyncSession) -> dict:
        """Download video."""
        result = await self.crawler.download_video(aweme_id, quality)
        return result or {"status": "failed", "message": "Download failed"}
