from fastapi import APIRouter, Depends

from app.auth.permissions import get_current_user
from app.users.models import User

from app.modules.gamification.schemas import (
    AchievementSummary,
    LeaderboardPage,
    QuestFrequency,
    QuestItem,
)

router = APIRouter(prefix="/api/v1/gamification", tags=["gamification"])


@router.get("/quests", response_model=list[QuestItem])
async def get_achievements(
    current_user: User = Depends(get_current_user),
):
    """Endpoint untuk mengambil seluruh quest mahasiswa beserta statusnya"""
    raise NotImplementedError


@router.get("/quests/{frequency}", response_model=list[QuestItem])
async def get_quests(
    frequency: QuestFrequency,
    current_user: User = Depends(get_current_user),
):
    """
    Endpoint untuk mengambil quest berdasarkan frekuensi
    """
    raise NotImplementedError


@router.get("/summary", response_model=AchievementSummary)
async def get_quests(
    current_user: User = Depends(get_current_user),
):
    """
    Endpoint untuk mengambil rangkuman pencapaian mahasiswa.
    """
    raise NotImplementedError


@router.get("/summary", response_model=LeaderboardPage)
async def get_leaderboard(
    current_user: User = Depends(get_current_user),
):
    """
    Endpoint untuk mengambil seluruh data page leaderboard mencakup ranking global dan ranking mahasiswa terlogin
    """
    raise NotImplementedError