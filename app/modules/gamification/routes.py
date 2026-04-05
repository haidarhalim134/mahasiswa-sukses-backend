from fastapi import APIRouter

from app.modules.gamification.schemas import AchievementSummary, LeaderboardPage, QuestFrequency, QuestItem

router = APIRouter(prefix="/api/v1/gamification", tags=["gamification"])

@router.get("/quests", response_model=list[QuestItem])
async def get_achievements():
    """Endpoint untuk mengambil seluruh quest mahasiswa beserta statusnya"""
    raise NotImplementedError

@router.get("/quests/{frequency}", response_model=list[QuestItem])
async def get_quests(frequency: QuestFrequency):
    """
    Endpoint untuk mengambil quest berdasarkan frekuensi
    """
    raise NotImplementedError

@router.get("/summary", response_model=AchievementSummary)
async def get_quests():
    """
    Endpoint untuk mengambil rangkuman pencapaian mahasiswa.
    """
    raise NotImplementedError

@router.get("/summary", response_model=LeaderboardPage)
async def get_leaderboard():
    """
    Endpoint untuk mengambil seluruh data page leaderboard mencakup ranking global dan ranking mahasiswa terlogin
    """
    raise NotImplementedError