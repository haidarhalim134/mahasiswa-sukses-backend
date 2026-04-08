from datetime import datetime, timezone
from typing import Optional, List
from uuid import UUID

from sqlmodel import select, delete, update, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.progress_tracking.models import Task
from app.modules.progress_tracking.schemas import TaskCreate, TaskProgress, TaskCategory, TaskPriority


def to_utc(dt: datetime) -> datetime:
    """Ensure datetime is stored in UTC"""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


async def create_task_service(
    db: AsyncSession,
    task: TaskCreate,
    user_id: UUID,
) -> Task:
    new_task = Task(
        user_id=user_id,
        title=task.title,
        description=task.description,
        category=task.category,
        priority=task.priority,
        deadline=to_utc(task.deadline),
        progress=TaskProgress.TODO,
        is_completed=False,
    )

    db.add(new_task)
    await db.commit()
    await db.refresh(new_task)
    return new_task


async def get_tasks_service(
    db: AsyncSession,
    user_id: UUID,
    category: Optional[TaskCategory] = None,
) -> List[Task]:
    query = select(Task)

    query = query.where(Task.user_id == user_id)
    if category:
        query = query.where(Task.category == category)

    result = await db.execute(query)
    return result.scalars()._allrows()


async def get_task_summary_service(
    db: AsyncSession,
    user_id: UUID,
):
    total_completed = await db.scalar(
        select(func.count()).select_from(Task).where(Task.is_completed == True, Task.user_id == user_id)
    )

    todo = await db.scalar(
        select(func.count()).select_from(Task).where(Task.progress == TaskProgress.TODO, Task.user_id == user_id)
    )

    on_progress = await db.scalar(
        select(func.count()).select_from(Task).where(Task.progress == TaskProgress.ON_PROGRESS, Task.user_id == user_id)
    )

    high_priority = await db.scalar(
        select(func.count()).select_from(Task).where(Task.priority == TaskPriority.TINGGI, Task.user_id == user_id)
    )

    return {
        "task_completed": total_completed or 0,
        "todo": todo or 0,
        "on_progress": on_progress or 0,
        "high_priority": high_priority or 0,
    }


async def update_task_progress_service(
    db: AsyncSession,
    task_id: int,
    progress: TaskProgress,
):
    is_completed = progress == TaskProgress.DONE

    _ = await db.execute(
        update(Task)
        .where(Task.id == task_id)
        .values(
            progress=progress,
            is_completed=is_completed,
        )
    )

    await db.commit()


async def delete_task_service(
    db: AsyncSession,
    task_id: int,
):
    await db.execute(
        delete(Task).where(Task.id == task_id)
    )
    await db.commit()