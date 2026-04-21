from fastapi import APIRouter, Body, Depends, Response, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.scheduler import TaskData, TaskGroup
from app.db.session import get_db
from app.modules.gamification.schemas import QuestFrequency
from app.modules.gamification.services import reset_quests_by_frequency


router = APIRouter(prefix="/api/v1/task", tags=["task"], include_in_schema=False)

@router.post("/execute")
async def execute_task(
    task_token: str,
    task_data: TaskData = Body(...),
    db: AsyncSession = Depends(get_db),
):
    if task_token != settings.task_token:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid task token",
        )

    match task_data.task_group:
        case TaskGroup.QUEST_RESET:
            await reset_quests_by_frequency(db, task_data.frequency)

        case TaskGroup.QUIZ:
            pass

        case TaskGroup.NOTIFICATION:
            pass

        case _:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unknown task_group: {task_data.task_group}",
            )