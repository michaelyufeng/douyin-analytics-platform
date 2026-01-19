"""
Search-related business logic service.
"""
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.crawler import DouyinCrawler


class SearchService:
    """Service for search operations."""

    def __init__(self):
        self.crawler = DouyinCrawler()

    async def search_video(
        self,
        keyword: str,
        cursor: int,
        count: int,
        sort_type: int,
        publish_time: int,
        db: AsyncSession
    ) -> dict:
        """Search for videos."""
        data = await self.crawler.search_video(keyword, cursor, count, sort_type, publish_time)
        return data or {"videos": [], "cursor": 0, "has_more": False}

    async def search_user(self, keyword: str, cursor: int, count: int, db: AsyncSession) -> dict:
        """Search for users."""
        data = await self.crawler.search_user(keyword, cursor, count)
        return data or {"users": [], "cursor": 0, "has_more": False}

    async def search_live(self, keyword: str, cursor: int, count: int, db: AsyncSession) -> dict:
        """Search for live streams."""
        data = await self.crawler.search_live(keyword, cursor, count)
        return data or {"lives": [], "cursor": 0, "has_more": False}

    async def get_search_suggest(self, keyword: str, db: AsyncSession) -> dict:
        """Get search suggestions."""
        data = await self.crawler.get_search_suggest(keyword)
        return data or {"suggestions": []}

    async def get_trending_searches(self, db: AsyncSession) -> dict:
        """Get trending search keywords."""
        data = await self.crawler.get_trending_searches()
        return data or {"trends": []}
