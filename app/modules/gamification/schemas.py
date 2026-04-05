from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel

from app.modules.quiz.schemas import QuizDifficulty

class QuestFrequency(str, Enum):
    DAILY = "harian"
    WEEKLY = "mingguan"

class QuestType(str, Enum):
    QUEST = "Quest"
    FORUM = "Forum"
    STREAK = "Streak"

class QuestItem(BaseModel):
    id: int
    title: str
    description: str
    quest_type: QuestType
    xp_reward: int
    difficulty: QuizDifficulty  # Reusing from previous section
    progress_text: str  # e.g., "40/60 Menit" or "100%"
    progress_percentage: int
    is_completed: bool

class AchievementSummary(BaseModel):
    total_quest: int
    total_quest_completed: int
    total_xp_earned: int

class LeaderboardItem(BaseModel):
    name: str
    avatar_url: str
    xp: int

class LeaderboardPage(BaseModel):
    user_rank: int
    user_total_xp: int
    top_global: list[LeaderboardItem]
    top_friends: list[LeaderboardItem]
