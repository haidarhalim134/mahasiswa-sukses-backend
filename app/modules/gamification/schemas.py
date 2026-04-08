from datetime import date, datetime
from enum import Enum
from typing import Optional, TypedDict
from pydantic import BaseModel

from app.modules.quiz.schemas import QuizDifficulty
from app.users.schemas import PublicUserView

class QuestFrequency(str, Enum):
    DAILY = "harian"
    WEEKLY = "mingguan"

class AchievementType(str, Enum):
    QUEST = "quest"
    FORUM = "forum"
    STREAK = "streak"

class QuestEvent(str, Enum):
    USER_LOGIN = "user_login"
    COMPLETE_TASK = "complete_task"
    COMPLETE_QUEST = "complete_quest"
    RECEIVE_LIKE = "receive_like"
    STAY_1_HOUR = "stay_1_hour"

class QuestItem(BaseModel):
    # id: int
    title: str
    description: str
    frequency: QuestFrequency
    xp_reward: int
    difficulty: QuizDifficulty  # Reusing from previous section
    progress_percentage: int
    is_completed: bool

class AchievementItem(BaseModel):
    # id: int
    title: str
    description: str
    type: AchievementType
    xp_reward: int
    difficulty: QuizDifficulty 
    progress_percentage: int
    is_completed: bool
    completion_date: date | None

class AchievementSummary(BaseModel):
    total_quest: int
    total_quest_completed: int
    total_xp_earned: int
    current_ranking: int
    current_streak: int

class LeaderboardItem(BaseModel):
    user: PublicUserView
    xp: int
    rank: int

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

class AchievementDef(TypedDict):
    id: str
    title: str
    description: str
    event: QuestEvent
    type: AchievementType
    target: int
    difficulty: QuizDifficulty
    xp_reward: int