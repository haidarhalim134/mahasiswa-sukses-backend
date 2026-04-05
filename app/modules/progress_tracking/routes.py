
from typing import Optional
from fastapi import APIRouter

from app.modules.progress_tracking.schemas import TaskCategory, TaskCreate, TaskProgress, TaskRead, TaskSummary

router = APIRouter(prefix="/api/v1/progress-tracking", tags=["progress tracking"])

@router.get("/summary", response_model=TaskSummary)
async def get_task_summary():
    """Endpoint untuk mengambil data rangkuman task seperti total task dan total task prioritas tinggi"""
    raise NotImplementedError

@router.get("/tasks", response_model=list[TaskRead])
async def get_tasks(category: Optional[TaskCategory] = None):
    """Endpoint untuk mengambil list task mahasiswa"""
    raise NotImplementedError

@router.post("/tasks", response_model=TaskRead, status_code=201)
async def create_task(task: TaskCreate):
    """Endpoint untuk membuat task baru"""
    raise NotImplementedError

@router.post("/tasks/{task_id}/update_progress/{progress}")
async def update_task_progress(task_id: int, progress: TaskProgress):
    """Endpoint untuk memperbarui progress task"""
    raise NotImplementedError

@router.delete("/tasks/{task_id}")
async def delete_task(task_id: int):
    """Endpoint untuk menghapus task dari list"""
    raise NotImplementedError