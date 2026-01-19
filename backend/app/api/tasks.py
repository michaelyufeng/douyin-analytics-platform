"""
Task management API endpoints.
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.schemas.task import TaskCreate, TaskUpdate, TaskResponse
from app.services.task_manager import TaskManager

router = APIRouter()
task_manager = TaskManager()


@router.get("")
async def get_tasks(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    is_active: Optional[bool] = None,
    task_type: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """获取任务列表"""
    return await task_manager.get_tasks(skip, limit, is_active, task_type, db)


@router.post("", response_model=TaskResponse)
async def create_task(
    task: TaskCreate,
    db: AsyncSession = Depends(get_db)
):
    """创建任务"""
    return await task_manager.create_task(task, db)


@router.put("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: int,
    task: TaskUpdate,
    db: AsyncSession = Depends(get_db)
):
    """更新任务"""
    result = await task_manager.update_task(task_id, task, db)
    if not result:
        raise HTTPException(status_code=404, detail="Task not found")
    return result


@router.delete("/{task_id}")
async def delete_task(
    task_id: int,
    db: AsyncSession = Depends(get_db)
):
    """删除任务"""
    success = await task_manager.delete_task(task_id, db)
    if not success:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"message": "Task deleted successfully"}


@router.post("/{task_id}/run")
async def run_task(
    task_id: int,
    db: AsyncSession = Depends(get_db)
):
    """立即执行"""
    result = await task_manager.run_task(task_id, db)
    if not result:
        raise HTTPException(status_code=404, detail="Task not found")
    return result


@router.get("/{task_id}/logs")
async def get_task_logs(
    task_id: int,
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db)
):
    """获取日志"""
    return await task_manager.get_task_logs(task_id, limit, db)
