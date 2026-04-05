from fastapi import APIRouter

from app.modules.gamification.schemas import AchievementRead, QuestFrequency, QuestItem

router = APIRouter(prefix="/api/v1/gamification", tags=["gamification"])

@router.get("/achievements", response_model=list[AchievementRead])
async def get_achievements():
    """Returns all badges and their current progress (Achievement Status)."""
    raise NotImplementedError

@router.get("/quests/{frequency}", response_model=list[QuestItem], tags=["Quiz & Quest"])
async def get_quests(frequency: QuestFrequency):
    """
    Returns quests based on the toggle (Quest harian vs Quest Mingguan).
    Matches the 'Login Harian', 'Maraphon belajar', etc., cards.
    """
    raise NotImplementedError