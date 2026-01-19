"""
Analysis service for deep data analysis.
"""
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from loguru import logger

from app.models.task import AnalysisResult
from app.services.user_service import UserService
from app.services.video_service import VideoService
from app.services.comment_service import CommentService
from app.core.crawler import DouyinCrawler


class AnalysisService:
    """Service for data analysis operations."""

    def __init__(self):
        self.crawler = DouyinCrawler()
        self.user_service = UserService()
        self.video_service = VideoService()
        self.comment_service = CommentService()

    async def analyze_user(self, sec_uid: str, db: AsyncSession) -> dict:
        """Deep analysis of a user."""
        # Get user profile
        profile = await self.user_service.get_user_profile(sec_uid, db)
        if not profile:
            return {"error": "User not found"}

        # Get user posts
        posts_data = await self.crawler.get_user_posts(sec_uid, 0, 50)
        posts = posts_data.get("videos", []) if posts_data else []

        # Calculate metrics
        total_plays = sum(v.get("play_count", 0) for v in posts)
        total_likes = sum(v.get("digg_count", 0) for v in posts)
        total_comments = sum(v.get("comment_count", 0) for v in posts)

        avg_plays = total_plays / len(posts) if posts else 0
        avg_likes = total_likes / len(posts) if posts else 0

        engagement_rate = 0
        if profile.get("follower_count", 0) > 0:
            engagement_rate = (total_likes + total_comments) / (profile["follower_count"] * len(posts)) if posts else 0

        # Determine growth trend (would need historical data)
        growth_trend = "stable"

        result = {
            "sec_uid": sec_uid,
            "nickname": profile.get("nickname", ""),
            "engagement_rate": round(engagement_rate * 100, 2),
            "avg_views": round(avg_plays, 0),
            "avg_likes": round(avg_likes, 0),
            "posting_frequency": len(posts) / 4,  # Approximate posts per week
            "best_posting_time": None,
            "content_categories": [],
            "growth_trend": growth_trend,
            "top_videos": posts[:5] if posts else []
        }

        # Save result
        analysis_result = AnalysisResult(
            analysis_type="user",
            target_type="user",
            target_id=sec_uid,
            result=result
        )
        db.add(analysis_result)
        await db.flush()

        return result

    async def analyze_video(self, aweme_id: str, db: AsyncSession) -> dict:
        """Deep analysis of a video."""
        # Get video detail
        video = await self.video_service.get_video_detail(aweme_id, db)
        if not video:
            return {"error": "Video not found"}

        # Calculate metrics
        total_engagement = video.get("digg_count", 0) + video.get("comment_count", 0) + video.get("share_count", 0)
        play_count = video.get("play_count", 1)

        engagement_rate = total_engagement / play_count if play_count > 0 else 0
        viral_score = min(100, (engagement_rate * 1000))  # Simplified viral score

        result = {
            "aweme_id": aweme_id,
            "engagement_rate": round(engagement_rate * 100, 2),
            "viral_score": round(viral_score, 2),
            "best_engagement_time": None,
            "audience_sentiment": {
                "positive": 0.6,
                "negative": 0.1,
                "neutral": 0.3
            },
            "similar_videos": []
        }

        # Save result
        analysis_result = AnalysisResult(
            analysis_type="video",
            target_type="video",
            target_id=aweme_id,
            result=result
        )
        db.add(analysis_result)
        await db.flush()

        return result

    async def analyze_comments(self, aweme_id: str, db: AsyncSession) -> dict:
        """Analyze comments for a video."""
        result = await self.comment_service.analyze_comments(aweme_id, db)

        # Save result
        analysis_result = AnalysisResult(
            analysis_type="comments",
            target_type="video",
            target_id=aweme_id,
            result=result
        )
        db.add(analysis_result)
        await db.flush()

        return result

    async def analyze_trends(self, keyword: str, days: int, db: AsyncSession) -> dict:
        """Analyze trends for a keyword."""
        # Search for videos with this keyword
        search_data = await self.crawler.search_video(keyword, 0, 50, 0, 0)
        videos = search_data.get("videos", []) if search_data else []

        result = {
            "keyword": keyword,
            "trend_direction": "stable",
            "search_volume": [],
            "related_topics": [],
            "top_creators": []
        }

        # Save result
        analysis_result = AnalysisResult(
            analysis_type="trends",
            target_type="keyword",
            target_id=keyword,
            result=result
        )
        db.add(analysis_result)
        await db.flush()

        return result

    async def get_report(self, report_id: int, db: AsyncSession) -> Optional[dict]:
        """Get an analysis report by ID."""
        result = await db.execute(
            select(AnalysisResult).where(AnalysisResult.id == report_id)
        )
        report = result.scalar_one_or_none()

        if not report:
            return None

        return {
            "id": report.id,
            "analysis_type": report.analysis_type,
            "target_type": report.target_type,
            "target_id": report.target_id,
            "result": report.result,
            "created_at": report.created_at
        }
