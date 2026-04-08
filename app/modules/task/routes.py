from fastapi import APIRouter, Depends, Response, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.session import get_db
from app.modules.gamification.schemas import QuestFrequency
from app.modules.gamification.services import reset_quests_by_frequency


router = APIRouter(prefix="/api/v1/task", tags=["task"], include_in_schema=False)

@router.get("/daily")
async def daily(
    task_token: str,
    db: AsyncSession = Depends(get_db)
):
    if task_token != settings.task_token:
        raise HTTPException(403) 
    
    await reset_quests_by_frequency(db, QuestFrequency.DAILY)

@router.get("/weekly")
async def daily(
    task_token: str,
    db: AsyncSession = Depends(get_db)
):
    if task_token != settings.task_token:
        raise HTTPException(403) 
    
    await reset_quests_by_frequency(db, QuestFrequency.WEEKLY)