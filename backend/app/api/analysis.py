"""
Analysis related API endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.schemas.analysis import UserAnalysisRequest, VideoAnalysisRequest, CommentAnalysisRequest, TrendAnalysisRequest
from app.services.analysis_service import AnalysisService

router = APIRouter()
analysis_service = AnalysisService()


@router.post("/user")
async def analyze_user(
    request: UserAnalysisRequest,
    db: AsyncSession = Depends(get_db)
):
    """用户深度分析"""
    return await analysis_service.analyze_user(request.sec_uid, db)


@router.post("/video")
async def analyze_video(
    request: VideoAnalysisRequest,
    db: AsyncSession = Depends(get_db)
):
    """视频数据分析"""
    return await analysis_service.analyze_video(request.aweme_id, db)


@router.post("/comments")
async def analyze_comments(
    request: CommentAnalysisRequest,
    db: AsyncSession = Depends(get_db)
):
    """评论情感分析"""
    return await analysis_service.analyze_comments(request.aweme_id, db)


@router.post("/trends")
async def analyze_trends(
    request: TrendAnalysisRequest,
    db: AsyncSession = Depends(get_db)
):
    """趋势分析"""
    return await analysis_service.analyze_trends(request.keyword, request.days, db)


@router.get("/report/{report_id}")
async def get_analysis_report(
    report_id: int,
    db: AsyncSession = Depends(get_db)
):
    """获取分析报告"""
    result = await analysis_service.get_report(report_id, db)
    if not result:
        raise HTTPException(status_code=404, detail="Report not found")
    return result
