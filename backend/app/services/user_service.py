"""
User-related business logic service.
"""
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from loguru import logger

from app.models.user import User, UserSnapshot
from app.core.crawler import DouyinCrawler


class UserService:
    """Service for user-related operations."""

    def __init__(self):
        self.crawler = DouyinCrawler()

    async def get_user_profile(self, sec_uid: str, db: AsyncSession) -> Optional[dict]:
        """Get user profile from Douyin API and cache in database."""
        # Try to get from database first
        result = await db.execute(select(User).where(User.sec_uid == sec_uid))
        user = result.scalar_one_or_none()

        # Fetch fresh data from API
        try:
            profile_data = await self.crawler.get_user_profile(sec_uid)
            if profile_data:
                if user:
                    # Update existing user
                    for key, value in profile_data.items():
                        if hasattr(user, key):
                            setattr(user, key, value)
                else:
                    # Create new user
                    user = User(**profile_data)
                    db.add(user)
                await db.flush()
                await db.refresh(user)

                # Create snapshot
                snapshot = UserSnapshot(
                    user_id=user.id,
                    follower_count=user.follower_count,
                    following_count=user.following_count,
                    total_favorited=user.total_favorited,
                    aweme_count=user.aweme_count
                )
                db.add(snapshot)
        except Exception as e:
            logger.error(f"Error fetching user profile: {e}")
            if not user:
                return None

        return {
            "id": user.id,
            "sec_uid": user.sec_uid,
            "uid": user.uid,
            "nickname": user.nickname,
            "unique_id": user.unique_id,
            "signature": user.signature,
            "avatar_url": user.avatar_url,
            "follower_count": user.follower_count,
            "following_count": user.following_count,
            "total_favorited": user.total_favorited,
            "aweme_count": user.aweme_count,
            "is_verified": user.is_verified,
            "verify_info": user.verify_info,
            "region": user.region,
            "created_at": user.created_at,
            "updated_at": user.updated_at
        }

    async def get_user_posts(self, sec_uid: str, cursor: int, count: int, db: AsyncSession) -> dict:
        """Get user's video posts."""
        data = await self.crawler.get_user_posts(sec_uid, cursor, count)
        return data or {"videos": [], "cursor": 0, "has_more": False}

    async def get_user_likes(self, sec_uid: str, cursor: int, count: int, db: AsyncSession) -> dict:
        """Get user's liked videos."""
        data = await self.crawler.get_user_likes(sec_uid, cursor, count)
        return data or {"videos": [], "cursor": 0, "has_more": False}

    async def get_user_collections(self, sec_uid: str, cursor: int, count: int, db: AsyncSession) -> dict:
        """Get user's collected videos."""
        data = await self.crawler.get_user_collections(sec_uid, cursor, count)
        return data or {"collections": [], "cursor": 0, "has_more": False}

    async def get_user_following(self, sec_uid: str, cursor: int, count: int, db: AsyncSession) -> dict:
        """Get user's following list."""
        data = await self.crawler.get_user_following(sec_uid, cursor, count)
        return data or {"users": [], "cursor": 0, "has_more": False}

    async def get_user_followers(self, sec_uid: str, cursor: int, count: int, db: AsyncSession) -> dict:
        """Get user's followers list."""
        data = await self.crawler.get_user_followers(sec_uid, cursor, count)
        return data or {"users": [], "cursor": 0, "has_more": False}

    async def get_user_mixes(self, sec_uid: str, cursor: int, count: int, db: AsyncSession) -> dict:
        """Get user's video mixes/collections."""
        data = await self.crawler.get_user_mixes(sec_uid, cursor, count)
        return data or {"mixes": [], "cursor": 0, "has_more": False}

    async def get_user_history(self, user_id: int, days: int, db: AsyncSession) -> dict:
        """Get user's follower history."""
        from datetime import datetime, timedelta
        from sqlalchemy import and_

        start_date = datetime.utcnow() - timedelta(days=days)
        result = await db.execute(
            select(UserSnapshot)
            .where(
                and_(
                    UserSnapshot.user_id == user_id,
                    UserSnapshot.snapshot_time >= start_date
                )
            )
            .order_by(UserSnapshot.snapshot_time)
        )
        snapshots = result.scalars().all()

        return {
            "user_id": user_id,
            "snapshots": [
                {
                    "follower_count": s.follower_count,
                    "following_count": s.following_count,
                    "total_favorited": s.total_favorited,
                    "aweme_count": s.aweme_count,
                    "snapshot_time": s.snapshot_time.isoformat()
                }
                for s in snapshots
            ]
        }

    async def compare_users(self, sec_uids: List[str], db: AsyncSession) -> dict:
        """Compare multiple users."""
        users = []
        for sec_uid in sec_uids:
            profile = await self.get_user_profile(sec_uid, db)
            if profile:
                users.append(profile)

        # Calculate comparison metrics
        comparison = {}
        if users:
            comparison = {
                "max_followers": max(u["follower_count"] for u in users),
                "min_followers": min(u["follower_count"] for u in users),
                "avg_followers": sum(u["follower_count"] for u in users) / len(users),
                "total_videos": sum(u["aweme_count"] for u in users)
            }

        return {"users": users, "comparison": comparison}

    async def batch_get_users(self, sec_uids: List[str], db: AsyncSession) -> dict:
        """Batch get multiple users."""
        users = []
        for sec_uid in sec_uids:
            profile = await self.get_user_profile(sec_uid, db)
            if profile:
                users.append(profile)
        return {"users": users, "total": len(users)}
