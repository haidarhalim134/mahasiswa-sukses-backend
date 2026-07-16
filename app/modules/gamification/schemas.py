from datetime import date, datetime
from enum import Enum
from typing import Callable, Optional, TypedDict
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

class QuestOnlyEvent(str, Enum):
    USER_LOGIN = "user_login"
    COMPLETE_TASK = "complete_task"
    COMPLETE_QUEST = "complete_quest"
    RECEIVE_LIKE = "receive_like"
    STAY_1_HOUR = "stay_1_hour"
    STAY_10_MIN = "stay_10_min"
    POST_COMMENT = 'post_comment'
    # post comment on a forum post in 'bantuan' category
    POST_COMMENT_ON_HELP = 'post_comment_on_help'

class QuestEvent(str, Enum):
    USER_LOGIN = "user_login"
    USER_LOGIN_STREAK = "user_login_streak"
    COMPLETE_TASK = "complete_task"
    COMPLETE_QUEST = "complete_quest"
    RECEIVE_LIKE = "receive_like"
    STAY_1_HOUR = "stay_1_hour"
    STAY_10_MIN = "stay_10_min"
    POST_COMMENT = 'post_comment'
    # post comment on a forum post in 'bantuan' category
    POST_COMMENT_ON_HELP = 'post_comment_on_help'

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
    current_level: int
    total_xp_earned: int
    current_ranking: int
    current_streak: int

    current_level_xp: int
    next_level_required_xp_diff : int

class LeaderboardItem(BaseModel):
    user: PublicUserView
    xp: int
    rank: int
    level: int

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

class HistoryItem(BaseModel):
    id: int
    title: str
    xp_reward: int
    type: str
    completed_at: datetime

class QuestCreate(BaseModel):
    title: str
    description: str
    event: QuestOnlyEvent
    target: int = 1
    difficulty: QuizDifficulty
    frequency: QuestFrequency
    xp_reward: int
    is_active: bool = True

class QuestUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    event: Optional[QuestOnlyEvent] = None
    target: Optional[int] = None
    difficulty: Optional[QuizDifficulty] = None
    frequency: Optional[QuestFrequency] = None
    xp_reward: Optional[int] = None
    is_active: Optional[bool] = None