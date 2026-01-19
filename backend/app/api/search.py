"""
Search related API endpoints.
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.services.search_service import SearchService

router = APIRouter()
search_service = SearchService()


@router.get("/video")
async def search_video(
    keyword: str = Query(..., min_length=1),
    cursor: int = Query(0, ge=0),
    count: int = Query(20, ge=1, le=50),
    sort_type: int = Query(0, ge=0, le=3),
    publish_time: int = Query(0, ge=0, le=4),
    db: AsyncSession = Depends(get_db)
):
    """搜索视频"""
    return await search_service.search_video(keyword, cursor, count, sort_type, publish_time, db)


@router.get("/user")
async def search_user(
    keyword: str = Query(..., min_length=1),
    cursor: int = Query(0, ge=0),
    count: int = Query(20, ge=1, le=50),
    db: AsyncSession = Depends(get_db)
):
    """搜索用户"""
    return await search_service.search_user(keyword, cursor, count, db)


@router.get("/live")
async def search_live(
    keyword: str = Query(..., min_length=1),
    cursor: int = Query(0, ge=0),
    count: int = Query(20, ge=1, le=50),
    db: AsyncSession = Depends(get_db)
):
    """搜索直播"""
    return await search_service.search_live(keyword, cursor, count, db)


@router.get("/suggest")
async def get_search_suggest(
    keyword: str = Query(..., min_length=1),
    db: AsyncSession = Depends(get_db)
):
    """搜索建议"""
    return await search_service.get_search_suggest(keyword, db)


@router.get("/trending")
async def get_trending_searches(
    db: AsyncSession = Depends(get_db)
):
    """热门搜索词"""
    return await search_service.get_trending_searches(db)
