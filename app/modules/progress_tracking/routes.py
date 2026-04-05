
from typing import Optional
from fastapi import APIRouter

from app.modules.progress_tracking.schemas import TaskCategory, TaskCreate, TaskRead

router = APIRouter(prefix="/api/v1/progress-tracking", tags=["progress tracking"])

@router.get("/tasks", response_model=list[TaskRead])
async def get_tasks(category: Optional[TaskCategory] = None):
    """Returns the list of tasks, optionally filtered by category."""
    raise NotImplementedError

@router.post("/tasks", response_model=TaskRead, status_code=201)
async def create_task(task: TaskCreate):
    """Creates a new task via the 'Tambah Tugas' pop-up."""
    raise NotImplementedError

@router.post("/tasks/{task_id}/complete")
async def toggle_task_completion(task_id: int):
    """Marks a task as finished or unfinished."""
    raise NotImplementedError

@router.delete("/tasks/{task_id}")
async def delete_task(task_id: int):
    """Removes a task from the list."""
    raise NotImplementedError