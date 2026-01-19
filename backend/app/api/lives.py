"""
Live streaming related API endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.schemas.live import LiveInfo, LiveRecordRequest
from app.services.live_service import LiveService

router = APIRouter()
live_service = LiveService()


@router.get("/info/{room_id}")
async def get_live_info(
    room_id: str,
    db: AsyncSession = Depends(get_db)
):
    """获取直播间信息"""
    result = await live_service.get_live_info(room_id, db)
    if not result:
        raise HTTPException(status_code=404, detail="Live room not found")
    return result


@router.get("/by-user/{sec_uid}")
async def get_live_by_user(
    sec_uid: str,
    db: AsyncSession = Depends(get_db)
):
    """通过用户获取直播"""
    return await live_service.get_live_by_user(sec_uid, db)


@router.get("/danmaku/{room_id}")
async def get_live_danmaku(
    room_id: str,
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db)
):
    """获取历史弹幕"""
    return await live_service.get_live_danmaku(room_id, limit, db)


@router.get("/ranking")
async def get_live_ranking(
    count: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """直播热门榜"""
    return await live_service.get_live_ranking(count, db)


@router.post("/record")
async def start_recording(
    request: LiveRecordRequest,
    db: AsyncSession = Depends(get_db)
):
    """开始录制"""
    return await live_service.start_recording(request.room_id, db)
