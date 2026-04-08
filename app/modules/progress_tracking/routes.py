from typing import Optional
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.permissions import get_current_user
from app.db.session import get_db
from app.modules.progress_tracking.services import create_task_service, delete_task_service, get_task_summary_service, get_tasks_service, update_task_progress_service
from app.users.models import User
from app.modules.progress_tracking.schemas import TaskCategory, TaskCreate, TaskProgress, TaskRead, TaskSummary

router = APIRouter(prefix="/api/v1/progress-tracking", tags=["progress tracking"])


@router.get("/summary", response_model=TaskSummary)
async def get_task_summary(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Endpoint untuk mengambil data rangkuman task seperti total task dan total task prioritas tinggi"""
    return await get_task_summary_service(db, current_user.id)


@router.get("/tasks", response_model=list[TaskRead])
async def get_tasks(
    category: Optional[TaskCategory] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Endpoint untuk mengambil list task mahasiswa"""
    return await get_tasks_service(db, current_user.id, category)


@router.post("/tasks", response_model=TaskRead, status_code=201)
async def create_task(
    task: TaskCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Endpoint untuk membuat task baru"""
    return await create_task_service(db, task, current_user.id)


@router.post("/tasks/{task_id}/update_progress/{progress}")
async def update_task_progress(
    task_id: int,
    progress: TaskProgress,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Endpoint untuk memperbarui progress task"""
    return await update_task_progress_service(db, task_id, progress)


@router.delete("/tasks/{task_id}")
async def delete_task(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Endpoint untuk menghapus task dari list"""
    return await delete_task_service(db, task_id)