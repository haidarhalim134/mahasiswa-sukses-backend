from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.permissions import get_current_user
from app.db.session import get_db
from app.modules.gamification.services import generate_leaderboard, get_user_achievements, get_user_quests, get_user_rank
from app.users.models import User

from app.modules.gamification.schemas import (
    AchievementItem,
    AchievementSummary,
    AchievementType,
    LeaderboardPage,
    QuestFrequency,
    QuestItem,
)

router = APIRouter(prefix="/api/v1/gamification", tags=["gamification"])


@router.get("/achievement", response_model=list[AchievementItem])
async def get_achievements(
    achievement_type: AchievementType | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Endpoint untuk mengambil achievement mahasiswa berdasarkan tipe"""
    return await get_user_achievements(db, current_user.id, achievement_type)


@router.get("/quests", response_model=list[QuestItem])
async def get_quests(
    frequency: QuestFrequency | None = None,
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
    db: AsyncSession = Depends(get_db)
):
    """
    Endpoint untuk mengambil rangkuman pencapaian mahasiswa.
    """

    # TODO: optimize maybe
    daily_quest = await get_user_quests(db, current_user.id, QuestFrequency.DAILY)
    weekly_quest = await get_user_quests(db, current_user.id, QuestFrequency.WEEKLY)
    all_quest = daily_quest + weekly_quest
    total_quest = len(all_quest)
    total_quest_completed = len([x for x in all_quest if x.is_completed])

    return AchievementSummary(
        total_quest=total_quest,
        total_quest_completed=total_quest_completed,
        total_xp_earned=current_user.total_xp
    )


@router.get("/leaderboard", response_model=LeaderboardPage)
async def get_leaderboard(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Endpoint untuk mengambil seluruh data page leaderboard mencakup ranking global dan ranking mahasiswa terlogin
    """
    return LeaderboardPage(
        user_rank=await get_user_rank(db, current_user.id),
        user_total_xp=current_user.total_xp,
        top_global=await generate_leaderboard(db, 100),
        # TODO: no friends feature yet, update later
        top_friends=await generate_leaderboard(db, 100) 
    )