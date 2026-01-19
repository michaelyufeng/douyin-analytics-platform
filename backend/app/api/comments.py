"""
Comment-related API endpoints.
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.services.comment_service import CommentService

router = APIRouter()
comment_service = CommentService()


@router.get("/video/{aweme_id}")
async def get_comments_by_video(
    aweme_id: str,
    cursor: int = Query(0, ge=0),
    count: int = Query(20, ge=1, le=50),
    db: AsyncSession = Depends(get_db)
):
    """获取视频评论"""
    return await comment_service.get_comments_by_video(aweme_id, cursor, count, db)


@router.get("/replies/{comment_id}")
async def get_comment_replies(
    comment_id: str,
    cursor: int = Query(0, ge=0),
    count: int = Query(20, ge=1, le=50),
    db: AsyncSession = Depends(get_db)
):
    """获取评论回复"""
    return await comment_service.get_comment_replies(comment_id, cursor, count, db)


@router.get("/analysis/{aweme_id}")
async def analyze_comments(
    aweme_id: str,
    db: AsyncSession = Depends(get_db)
):
    """评论情感分析"""
    return await comment_service.analyze_comments(aweme_id, db)
