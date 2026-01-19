"""
User-related API endpoints.
"""
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.schemas.user import UserProfile, UserResponse, UserCompareRequest, BatchUserRequest
from app.services.user_service import UserService

router = APIRouter()
user_service = UserService()


@router.get("/profile/{sec_uid}", response_model=UserResponse)
async def get_user_profile(
    sec_uid: str,
    db: AsyncSession = Depends(get_db)
):
    """获取用户资料"""
    result = await user_service.get_user_profile(sec_uid, db)
    if not result:
        raise HTTPException(status_code=404, detail="User not found")
    return result


@router.get("/posts/{sec_uid}")
async def get_user_posts(
    sec_uid: str,
    cursor: int = Query(0, ge=0),
    count: int = Query(20, ge=1, le=50),
    db: AsyncSession = Depends(get_db)
):
    """获取用户作品"""
    return await user_service.get_user_posts(sec_uid, cursor, count, db)


@router.get("/likes/{sec_uid}")
async def get_user_likes(
    sec_uid: str,
    cursor: int = Query(0, ge=0),
    count: int = Query(20, ge=1, le=50),
    db: AsyncSession = Depends(get_db)
):
    """获取用户喜欢"""
    return await user_service.get_user_likes(sec_uid, cursor, count, db)


@router.get("/collections/{sec_uid}")
async def get_user_collections(
    sec_uid: str,
    cursor: int = Query(0, ge=0),
    count: int = Query(20, ge=1, le=50),
    db: AsyncSession = Depends(get_db)
):
    """获取用户收藏"""
    return await user_service.get_user_collections(sec_uid, cursor, count, db)


@router.get("/following/{sec_uid}")
async def get_user_following(
    sec_uid: str,
    cursor: int = Query(0, ge=0),
    count: int = Query(20, ge=1, le=50),
    db: AsyncSession = Depends(get_db)
):
    """获取关注列表"""
    return await user_service.get_user_following(sec_uid, cursor, count, db)


@router.get("/followers/{sec_uid}")
async def get_user_followers(
    sec_uid: str,
    cursor: int = Query(0, ge=0),
    count: int = Query(20, ge=1, le=50),
    db: AsyncSession = Depends(get_db)
):
    """获取粉丝列表"""
    return await user_service.get_user_followers(sec_uid, cursor, count, db)


@router.get("/mixes/{sec_uid}")
async def get_user_mixes(
    sec_uid: str,
    cursor: int = Query(0, ge=0),
    count: int = Query(20, ge=1, le=50),
    db: AsyncSession = Depends(get_db)
):
    """获取用户合集"""
    return await user_service.get_user_mixes(sec_uid, cursor, count, db)


@router.get("/history/{user_id}")
async def get_user_history(
    user_id: int,
    days: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_db)
):
    """获取粉丝历史"""
    return await user_service.get_user_history(user_id, days, db)


@router.post("/compare")
async def compare_users(
    request: UserCompareRequest,
    db: AsyncSession = Depends(get_db)
):
    """用户对比分析"""
    return await user_service.compare_users(request.sec_uids, db)


@router.post("/batch")
async def batch_get_users(
    request: BatchUserRequest,
    db: AsyncSession = Depends(get_db)
):
    """批量获取用户"""
    return await user_service.batch_get_users(request.sec_uids, db)
