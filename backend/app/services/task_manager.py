"""
Task management service.
"""
from typing import Optional, List
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from loguru import logger

from app.models.task import MonitorTask, TaskLog
from app.schemas.task import TaskCreate, TaskUpdate


class TaskManager:
    """Service for managing monitoring tasks."""

    async def get_tasks(
        self,
        skip: int,
        limit: int,
        is_active: Optional[bool],
        task_type: Optional[str],
        db: AsyncSession
    ) -> dict:
        """Get list of tasks with filters."""
        query = select(MonitorTask)

        conditions = []
        if is_active is not None:
            conditions.append(MonitorTask.is_active == is_active)
        if task_type:
            conditions.append(MonitorTask.task_type == task_type)

        if conditions:
            query = query.where(and_(*conditions))

        query = query.offset(skip).limit(limit).order_by(MonitorTask.created_at.desc())
        result = await db.execute(query)
        tasks = result.scalars().all()

        # Count total
        count_query = select(MonitorTask)
        if conditions:
            count_query = count_query.where(and_(*conditions))
        count_result = await db.execute(count_query)
        total = len(count_result.scalars().all())

        return {
            "tasks": [
                {
                    "id": t.id,
                    "task_type": t.task_type,
                    "target_id": t.target_id,
                    "target_name": t.target_name,
                    "interval_seconds": t.interval_seconds,
                    "is_active": t.is_active,
                    "last_run": t.last_run,
                    "next_run": t.next_run,
                    "config": t.config,
                    "created_at": t.created_at
                }
                for t in tasks
            ],
            "total": total,
            "skip": skip,
            "limit": limit
        }

    async def create_task(self, task: TaskCreate, db: AsyncSession) -> dict:
        """Create a new monitoring task."""
        db_task = MonitorTask(
            task_type=task.task_type,
            target_id=task.target_id,
            target_name=task.target_name,
            interval_seconds=task.interval_seconds,
            is_active=True,
            next_run=datetime.utcnow() + timedelta(seconds=task.interval_seconds),
            config=task.config.model_dump() if task.config else None
        )
        db.add(db_task)
        await db.flush()
        await db.refresh(db_task)

        return {
            "id": db_task.id,
            "task_type": db_task.task_type,
            "target_id": db_task.target_id,
            "target_name": db_task.target_name,
            "interval_seconds": db_task.interval_seconds,
            "is_active": db_task.is_active,
            "last_run": db_task.last_run,
            "next_run": db_task.next_run,
            "config": db_task.config,
            "created_at": db_task.created_at
        }

    async def update_task(self, task_id: int, task: TaskUpdate, db: AsyncSession) -> Optional[dict]:
        """Update an existing task."""
        result = await db.execute(select(MonitorTask).where(MonitorTask.id == task_id))
        db_task = result.scalar_one_or_none()

        if not db_task:
            return None

        update_data = task.model_dump(exclude_unset=True)
        if "config" in update_data and update_data["config"]:
            update_data["config"] = update_data["config"].model_dump()

        for key, value in update_data.items():
            setattr(db_task, key, value)

        await db.flush()
        await db.refresh(db_task)

        return {
            "id": db_task.id,
            "task_type": db_task.task_type,
            "target_id": db_task.target_id,
            "target_name": db_task.target_name,
            "interval_seconds": db_task.interval_seconds,
            "is_active": db_task.is_active,
            "last_run": db_task.last_run,
            "next_run": db_task.next_run,
            "config": db_task.config,
            "created_at": db_task.created_at
        }

    async def delete_task(self, task_id: int, db: AsyncSession) -> bool:
        """Delete a task."""
        result = await db.execute(select(MonitorTask).where(MonitorTask.id == task_id))
        db_task = result.scalar_one_or_none()

        if not db_task:
            return False

        await db.delete(db_task)
        return True

    async def run_task(self, task_id: int, db: AsyncSession) -> Optional[dict]:
        """Run a task immediately."""
        result = await db.execute(select(MonitorTask).where(MonitorTask.id == task_id))
        db_task = result.scalar_one_or_none()

        if not db_task:
            return None

        # Log the task run
        log = TaskLog(
            task_id=task_id,
            status="running",
            message="Task started manually"
        )
        db.add(log)

        # Update last_run and next_run
        db_task.last_run = datetime.utcnow()
        db_task.next_run = datetime.utcnow() + timedelta(seconds=db_task.interval_seconds)

        await db.flush()

        # In a real implementation, this would trigger the actual task execution
        return {
            "task_id": task_id,
            "status": "running",
            "message": "Task started"
        }

    async def get_task_logs(self, task_id: int, limit: int, db: AsyncSession) -> dict:
        """Get task execution logs."""
        result = await db.execute(
            select(TaskLog)
            .where(TaskLog.task_id == task_id)
            .order_by(TaskLog.timestamp.desc())
            .limit(limit)
        )
        logs = result.scalars().all()

        return {
            "task_id": task_id,
            "logs": [
                {
                    "task_id": l.task_id,
                    "status": l.status,
                    "message": l.message,
                    "data": l.data,
                    "timestamp": l.timestamp
                }
                for l in logs
            ],
            "total": len(logs)
        }
