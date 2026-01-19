"""
Ranking/hot list related business logic service.
"""
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.crawler import DouyinCrawler


class RankingService:
    """Service for ranking operations."""

    def __init__(self):
        self.crawler = DouyinCrawler()

    async def get_board_list(self, db: AsyncSession) -> dict:
        """Get available ranking boards."""
        data = await self.crawler.get_board_list()
        return data or {
            "boards": [
                {"id": "hot_search", "name": "热搜榜"},
                {"id": "hot_video", "name": "视频榜"},
                {"id": "hot_live", "name": "直播榜"},
                {"id": "hot_brand", "name": "品牌榜"},
                {"id": "hot_music", "name": "音乐榜"}
            ]
        }

    async def get_hot_list(self, board_type: str, db: AsyncSession) -> dict:
        """Get hot list by board type."""
        data = await self.crawler.get_hot_list(board_type)
        return data or {"items": [], "board_type": board_type}

    async def get_video_ranking(self, count: int, db: AsyncSession) -> dict:
        """Get video ranking."""
        data = await self.crawler.get_video_ranking(count)
        return data or {"videos": [], "total": 0}

    async def get_live_ranking(self, count: int, db: AsyncSession) -> dict:
        """Get live ranking."""
        data = await self.crawler.get_live_ranking(count)
        return data or {"lives": [], "total": 0}
