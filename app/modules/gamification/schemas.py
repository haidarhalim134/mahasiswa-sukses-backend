from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel

from app.modules.quiz.schemas import QuizDifficulty

class QuestFrequency(str, Enum):
    DAILY = "harian"
    WEEKLY = "mingguan"

class AchievementRead(BaseModel):
    id: int
    title: str
    description: str
    earned_date: Optional[datetime]
    progress_percentage: int

class QuestItem(BaseModel):
    id: int
    title: str
    description: str
    xp_reward: int
    difficulty: QuizDifficulty  # Reusing from previous section
    progress_text: str  # e.g., "40/60 Menit" or "100%"
    progress_percentage: int
    is_completed: bool