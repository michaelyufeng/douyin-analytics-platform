"""
Ranking/Hot list related API endpoints.
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.services.ranking_service import RankingService

router = APIRouter()
ranking_service = RankingService()


@router.get("/boards")
async def get_board_list(
    db: AsyncSession = Depends(get_db)
):
    """获取榜单列表"""
    return await ranking_service.get_board_list(db)


@router.get("/hot/{board_type}")
async def get_hot_list(
    board_type: str,
    db: AsyncSession = Depends(get_db)
):
    """获取热搜榜"""
    return await ranking_service.get_hot_list(board_type, db)


@router.get("/video")
async def get_video_ranking(
    count: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """视频榜"""
    return await ranking_service.get_video_ranking(count, db)


@router.get("/live")
async def get_live_ranking(
    count: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """直播榜"""
    return await ranking_service.get_live_ranking(count, db)
