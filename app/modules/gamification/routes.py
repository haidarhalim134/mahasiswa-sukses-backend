from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.permissions import get_current_user
from app.db.session import get_db
from app.modules.gamification.services import get_user_quests
from app.users.models import User

from app.modules.gamification.schemas import (
    AchievementItem,
    AchievementSummary,
    LeaderboardPage,
    QuestFrequency,
    QuestItem,
)

router = APIRouter(prefix="/api/v1/gamification", tags=["gamification"])


@router.get("/achievement/{achievement_type}", response_model=list[AchievementItem])
async def get_achievements(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Endpoint untuk mengambil achievement mahasiswa berdasarkan tipe"""
    raise NotImplementedError


@router.get("/quests/{frequency}", response_model=list[QuestItem])
async def get_quests(
    frequency: QuestFrequency,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Endpoint untuk mengambil quest berdasarkan frekuensi
    """
    return await get_user_quests(db, current_user.id, frequency)


@router.get("/summary", response_model=AchievementSummary)
async def get_gamification_summary(
    current_user: User = Depends(get_current_user),
):
    """
    Endpoint untuk mengambil rangkuman pencapaian mahasiswa.
    """
    raise NotImplementedError


@router.get("/leaderboard", response_model=LeaderboardPage)
async def get_leaderboard(
    current_user: User = Depends(get_current_user),
):
    """
    Endpoint untuk mengambil seluruh data page leaderboard mencakup ranking global dan ranking mahasiswa terlogin
    """
    raise NotImplementedError