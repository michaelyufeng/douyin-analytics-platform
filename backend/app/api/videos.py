"""
Video-related API endpoints.
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.schemas.video import VideoDetail, VideoParseRequest, VideoDownloadRequest
from app.services.video_service import VideoService

router = APIRouter()
video_service = VideoService()


@router.get("/detail/{aweme_id}")
async def get_video_detail(
    aweme_id: str,
    db: AsyncSession = Depends(get_db)
):
    """获取视频详情"""
    result = await video_service.get_video_detail(aweme_id, db)
    if not result:
        raise HTTPException(status_code=404, detail="Video not found")
    return result


@router.get("/comments/{aweme_id}")
async def get_video_comments(
    aweme_id: str,
    cursor: int = Query(0, ge=0),
    count: int = Query(20, ge=1, le=50),
    db: AsyncSession = Depends(get_db)
):
    """获取视频评论"""
    return await video_service.get_video_comments(aweme_id, cursor, count, db)


@router.get("/replies/{comment_id}")
async def get_comment_replies(
    comment_id: str,
    cursor: int = Query(0, ge=0),
    count: int = Query(20, ge=1, le=50),
    db: AsyncSession = Depends(get_db)
):
    """获取评论回复"""
    return await video_service.get_comment_replies(comment_id, cursor, count, db)


@router.get("/related/{aweme_id}")
async def get_related_videos(
    aweme_id: str,
    count: int = Query(20, ge=1, le=50),
    db: AsyncSession = Depends(get_db)
):
    """获取相关推荐"""
    return await video_service.get_related_videos(aweme_id, count, db)


@router.get("/mix/{mix_id}")
async def get_mix_videos(
    mix_id: str,
    cursor: int = Query(0, ge=0),
    count: int = Query(20, ge=1, le=50),
    db: AsyncSession = Depends(get_db)
):
    """获取合集视频"""
    return await video_service.get_mix_videos(mix_id, cursor, count, db)


@router.get("/history/{video_id}")
async def get_video_history(
    video_id: int,
    days: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_db)
):
    """获取数据历史"""
    return await video_service.get_video_history(video_id, days, db)


@router.post("/parse")
async def parse_video_url(
    request: VideoParseRequest,
    db: AsyncSession = Depends(get_db)
):
    """解析视频链接"""
    return await video_service.parse_video_url(request.url, db)


@router.post("/download")
async def download_video(
    request: VideoDownloadRequest,
    db: AsyncSession = Depends(get_db)
):
    """下载视频"""
    return await video_service.download_video(request.aweme_id, request.quality, db)
