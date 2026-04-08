from datetime import datetime
from enum import Enum
from typing import Optional, TypedDict
from pydantic import BaseModel

from app.modules.quiz.schemas import QuizDifficulty

class QuestFrequency(str, Enum):
    DAILY = "harian"
    WEEKLY = "mingguan"

class AchievementType(str, Enum):
    QUEST = "Quest"
    FORUM = "Forum"
    STREAK = "Streak"

class QuestEvent(str, Enum):
    USER_LOGIN = "user_login"
    COMPLETE_TASK = "complete_task"
    RECEIVE_LIKE = "receive_like"
    STAYED_10_MINS = "stayed_10_mins"

class QuestItem(BaseModel):
    id: int
    title: str
    description: str
    frequency: QuestFrequency
    xp_reward: int
    difficulty: QuizDifficulty  # Reusing from previous section
    progress_percentage: int
    is_completed: bool

class AchievementItem(BaseModel):
    id: int
    title: str
    description: str
    type: AchievementType
    xp_reward: int
    difficulty: QuizDifficulty 
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

class QuestDef(TypedDict):
    id: str
    title: str
    description: str
    event: QuestEvent
    target: int
    difficulty: QuizDifficulty
    frequency: QuestFrequency
    xp_reward: int