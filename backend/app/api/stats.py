"""
Statistics API endpoints.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime, timedelta

from app.db.database import get_db
from app.models.user import User
from app.models.video import Video, VideoSnapshot
from app.models.task import MonitorTask
from app.models.comment import Comment

router = APIRouter(prefix="/stats", tags=["statistics"])


@router.get("")
async def get_statistics(db: AsyncSession = Depends(get_db)):
    """Get platform statistics overview."""
    # Count users
    user_count = await db.execute(select(func.count()).select_from(User))
    users = user_count.scalar() or 0

    # Count videos
    video_count = await db.execute(select(func.count()).select_from(Video))
    videos = video_count.scalar() or 0

    # Count active tasks
    task_count = await db.execute(
        select(func.count()).select_from(MonitorTask).where(MonitorTask.is_active == True)
    )
    tasks = task_count.scalar() or 0

    # Count comments
    comment_count = await db.execute(select(func.count()).select_from(Comment))
    comments = comment_count.scalar() or 0

    return {
        "users": users,
        "videos": videos,
        "tasks": tasks,
        "comments": comments,
        "updated_at": datetime.now().isoformat()
    }


@router.get("/recent")
async def get_recent_activities(db: AsyncSession = Depends(get_db), limit: int = 10):
    """Get recent activities/events."""
    activities = []

    # Get recently added users
    recent_users = await db.execute(
        select(User)
        .order_by(User.created_at.desc())
        .limit(5)
    )
    for user in recent_users.scalars():
        activities.append({
            "type": "user_added",
            "text": f"采集用户 @{user.nickname or user.unique_id or user.sec_uid[:8]}",
            "time": user.created_at.isoformat() if user.created_at else None,
            "icon": "user"
        })

    # Get recently added videos
    recent_videos = await db.execute(
        select(Video)
        .order_by(Video.created_at.desc())
        .limit(5)
    )
    for video in recent_videos.scalars():
        desc_preview = (video.desc[:20] + "...") if video.desc and len(video.desc) > 20 else (video.desc or "无标题")
        activities.append({
            "type": "video_added",
            "text": f"采集视频 {desc_preview}",
            "time": video.created_at.isoformat() if video.created_at else None,
            "icon": "video"
        })

    # Get recent tasks
    recent_tasks = await db.execute(
        select(MonitorTask)
        .where(MonitorTask.last_run.isnot(None))
        .order_by(MonitorTask.last_run.desc())
        .limit(5)
    )
    for task in recent_tasks.scalars():
        activities.append({
            "type": "task_run",
            "text": f"任务 {task.target_name or task.target_id} 执行完成",
            "time": task.last_run.isoformat() if task.last_run else None,
            "icon": "task"
        })

    # Sort by time and return top N
    activities.sort(key=lambda x: x.get("time") or "", reverse=True)
    return {"activities": activities[:limit]}


@router.get("/trends")
async def get_data_trends(db: AsyncSession = Depends(get_db), days: int = 7):
    """Get data trends for the last N days."""
    trends = []
    today = datetime.now().date()

    for i in range(days):
        date = today - timedelta(days=i)
        start = datetime.combine(date, datetime.min.time())
        end = datetime.combine(date, datetime.max.time())

        # Count users added that day
        user_count = await db.execute(
            select(func.count()).select_from(User)
            .where(User.created_at >= start)
            .where(User.created_at <= end)
        )

        # Count videos added that day
        video_count = await db.execute(
            select(func.count()).select_from(Video)
            .where(Video.created_at >= start)
            .where(Video.created_at <= end)
        )

        trends.append({
            "date": date.isoformat(),
            "users": user_count.scalar() or 0,
            "videos": video_count.scalar() or 0
        })

    trends.reverse()  # Oldest first
    return {"trends": trends}
