from typing import Annotated
from uuid import UUID
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.permissions import get_current_user, get_current_user_id
from app.db.session import get_db
from app.modules.gamification.services import generate_friends_leaderboard, generate_leaderboard, get_user_achievements, get_user_history, get_user_quest_stats, get_user_quests, get_user_rank, progress_quest
from app.users.models import User

from app.modules.gamification.schemas import (
    AchievementItem,
    AchievementSummary,
    AchievementType,
    HistoryItem,
    LeaderboardPage,
    QuestEvent,
    QuestFrequency,
    QuestItem,
)
from app.users.service import update_last_seen

router = APIRouter(prefix="/api/v1/gamification", tags=["gamification"])


@router.get("/achievement", response_model=list[AchievementItem])
async def get_achievements(
    current_user_id: Annotated[UUID, Depends(get_current_user_id)],
    db: Annotated[AsyncSession, Depends(get_db)],
    achievement_type: AchievementType | None = None,
):
    """Endpoint untuk mengambil achievement mahasiswa berdasarkan tipe"""
    return await get_user_achievements(db, current_user_id, achievement_type)


@router.get("/quests", response_model=list[QuestItem])
async def get_quests(
    current_user_id: Annotated[UUID, Depends(get_current_user_id)],
    db: Annotated[AsyncSession, Depends(get_db)],
    frequency: QuestFrequency | None = None,
):
    """
    Endpoint untuk mengambil quest berdasarkan frekuensi
    """
    return await get_user_quests(db, current_user_id, frequency)


@router.get("/summary", response_model=AchievementSummary)
async def get_gamification_summary(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """
    Endpoint untuk mengambil rangkuman pencapaian mahasiswa.
    """
    total_quest, total_quest_completed = await get_user_quest_stats(db, current_user.id)

    return AchievementSummary(
        total_quest=total_quest,
        total_quest_completed=total_quest_completed,
        current_level=current_user.level,
        total_xp_earned=current_user.total_xp,
        current_ranking=await get_user_rank(db, current_user),
        current_streak=current_user.current_streak,

        current_level_xp=current_user.current_level_xp,
        next_level_required_xp_diff=current_user.xp_required_for_this_milestone
    )


@router.get("/leaderboard", response_model=LeaderboardPage)
async def get_leaderboard(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """
    Endpoint untuk mengambil seluruh data page leaderboard mencakup ranking global dan ranking mahasiswa terlogin
    """
    return LeaderboardPage(
        user_rank=await get_user_rank(db, current_user),
        user_total_xp=current_user.total_xp,
        top_global=await generate_leaderboard(db, current_user, 100),
        top_friends=await generate_friends_leaderboard(db, current_user, 100)
    )

@router.get("/history", response_model=list[HistoryItem])
async def get_history(
    current_user_id: Annotated[UUID, Depends(get_current_user_id)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """
    Endpoint untuk mengambil 50 item terakhir history quest dan achievement terselesaikan
    """
    return await get_user_history(db, current_user_id)

@router.post("/heartbeat")
async def heartbeat(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """
    Endpoint untuk progress quest stay di aplikasi dan membantu aplikasi membuat estimasi jumlah user online, panggil setiap 10 menit
    """

    await progress_quest(
        db=db,
        user=current_user,
        event=QuestEvent.STAY_1_HOUR
    )

    await progress_quest(
        db=db,
        user=current_user,
        event=QuestEvent.STAY_10_MIN
    )

    # since this is here might be wiser to move the hearbeat to its own analytics module since its not just about quest anymore
    await update_last_seen(
        db=db,
        user_id=current_user.id
    )