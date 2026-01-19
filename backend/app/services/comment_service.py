"""
Comment-related business logic service.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from app.core.crawler import DouyinCrawler


class CommentService:
    """Service for comment-related operations."""

    def __init__(self):
        self.crawler = DouyinCrawler()

    async def get_comments_by_video(self, aweme_id: str, cursor: int, count: int, db: AsyncSession) -> dict:
        """Get comments for a video."""
        data = await self.crawler.get_video_comments(aweme_id, cursor, count)
        return data or {"comments": [], "cursor": 0, "has_more": False, "total": 0}

    async def get_comment_replies(self, comment_id: str, cursor: int, count: int, db: AsyncSession) -> dict:
        """Get replies to a comment."""
        data = await self.crawler.get_comment_replies(comment_id, cursor, count)
        return data or {"replies": [], "cursor": 0, "has_more": False}

    async def analyze_comments(self, aweme_id: str, db: AsyncSession) -> dict:
        """Analyze comments sentiment and keywords."""
        # Fetch all comments first
        all_comments = []
        cursor = 0
        has_more = True

        while has_more and len(all_comments) < 500:  # Limit to 500 comments
            data = await self.crawler.get_video_comments(aweme_id, cursor, 50)
            if not data or not data.get("comments"):
                break
            all_comments.extend(data["comments"])
            cursor = data.get("cursor", 0)
            has_more = data.get("has_more", False)

        # Analyze comments (simplified analysis)
        positive_count = 0
        negative_count = 0
        neutral_count = 0

        positive_words = ["好", "棒", "赞", "喜欢", "爱", "厉害", "优秀", "漂亮", "帅", "美"]
        negative_words = ["差", "烂", "垃圾", "讨厌", "无聊", "假", "骗", "坑"]

        for comment in all_comments:
            content = comment.get("content", "")
            has_positive = any(word in content for word in positive_words)
            has_negative = any(word in content for word in negative_words)

            if has_positive and not has_negative:
                positive_count += 1
            elif has_negative and not has_positive:
                negative_count += 1
            else:
                neutral_count += 1

        total = len(all_comments) or 1

        return {
            "aweme_id": aweme_id,
            "total_comments": len(all_comments),
            "sentiment": {
                "positive": positive_count / total,
                "negative": negative_count / total,
                "neutral": neutral_count / total
            },
            "top_keywords": [],  # Would need NLP for proper keyword extraction
            "user_demographics": {}
        }
