from typing import Annotated
from uuid import UUID
from fastapi import APIRouter, Depends, Security, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.permissions import get_current_user, get_current_user_id, require_role
from app.db.session import get_db
from app.modules.gamification.models import Quest
from app.modules.gamification.services import create_quest_service, delete_quest_service, generate_friends_leaderboard, generate_leaderboard, get_quest_service, get_user_achievements, get_user_history, get_user_quest_stats, get_user_quests, get_user_rank, list_quests_service, progress_quest, set_active_service, update_quest_service
from app.users.models import Role, User

from app.modules.gamification.schemas import (
    AchievementItem,
    AchievementSummary,
    AchievementType,
    HistoryItem,
    LeaderboardPage,
    QuestCreate,
    QuestEvent,
    QuestFrequency,
    QuestItem,
    QuestUpdate,
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

## admin
@router.get("/list-all", response_model=list[Quest])
async def list_quests(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Security(require_role([Role.admin]), scopes=[Role.admin.value])],
    skip: int = 0,
    limit: int = 100,
):
    """
    Endpoint untuk mengambil semua daftar quest yang ada di dalam sistem.
    """
    return await list_quests_service(db=db, skip=skip, limit=limit)


@router.get("/get-one/{quest_id}", response_model=Quest)
async def get_quest(
    quest_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Security(require_role([Role.admin]), scopes=[Role.admin.value])],
):
    """
    Endpoint untuk mengambil informasi detail dari satu quest spesifik berdasarkan quest_id.
    """
    return await get_quest_service(quest_id=quest_id, db=db)


@router.post("/create", response_model=Quest)
async def create_quest(
    payload: QuestCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Security(require_role([Role.admin]), scopes=[Role.admin.value])],
):
    """
    Endpoint untuk membuat dan menambahkan quest baru ke dalam database berdasarkan payload yang dikirim.
    """
    return await create_quest_service(payload=payload, db=db)


@router.post("/{quest_id}/set-active")
async def set_active(
    quest_id: str,
    active: bool,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Security(require_role([Role.admin]), scopes=[Role.admin.value])],
):
    """
    Endpoint untuk mengaktifkan atau menonaktifkan status sebuah quest secara cepat tanpa mengubah data lainnya.
    """
    await set_active_service(quest_id=quest_id, active=active, db=db)
    return


@router.put("/{quest_id}", response_model=Quest)
async def update_quest(
    quest_id: str,
    payload: QuestUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Security(require_role([Role.admin]), scopes=[Role.admin.value])],
):
    """
    Endpoint untuk memperbarui data atau informasi pada quest yang sudah ada. Hanya bidang/field yang dikirim yang akan diperbarui.
    """
    return await update_quest_service(quest_id=quest_id, payload=payload, db=db)


@router.delete("/{quest_id}")
async def delete_quest(
    quest_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Security(require_role([Role.admin]), scopes=[Role.admin.value])],
):
    """
    Endpoint untuk menghapus data quest secara permanen dari database berdasarkan quest_id.
    """
    await delete_quest_service(quest_id=quest_id, db=db)
    return