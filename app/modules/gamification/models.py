from datetime import datetime, date
from typing import Optional
import uuid

from app.db.base import Base
from sqlmodel import Boolean, DateTime, Field, Column, Relationship
from sqlalchemy import String, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID

from app.modules.gamification.schemas import QuestFrequency, AchievementType
from app.modules.quiz.schemas import QuizDifficulty

USER_ID = "users.id"

class Quest(Base, table=True):
    __tablename__ = "quests"

    id: str = Field(
        default_factory=lambda: str(uuid.uuid4()), 
        primary_key=True, 
        index=True
    )
    title: str = Field(nullable=False)
    description: str = Field(nullable=False)
    event: str = Field(nullable=False) 
    target: int = Field(default=1, nullable=False)
    difficulty: QuizDifficulty = Field(sa_column=Column(String, nullable=False))
    frequency: QuestFrequency = Field(sa_column=Column(String, nullable=False))
    xp_reward: int = Field(nullable=False)

    user_quests: list["UserQuest"] = Relationship(back_populates="quest")
    
    is_active: bool = Field(sa_column=Column(Boolean, nullable=False, default=True))

class UserQuest(Base, table=True):

    id: Optional[int] = Field(default=None, primary_key=True)

    user_id: uuid.UUID = Field(
        sa_column=Column(UUID(as_uuid=True), ForeignKey(USER_ID), index=True, nullable=False)
    )

    quest_id: str = Field(
        sa_column=Column(String, ForeignKey("quests.id", ondelete="CASCADE"), index=True, nullable=False)
    )  

    progress: int = Field(default=0)  
    target: int = Field(default=1) 
    is_completed: bool = Field(default=False)

    frequency: QuestFrequency = Field(
        sa_column=Column(String, nullable=False),
    )

    last_progress_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(
            DateTime(timezone=True),
            nullable=True
        )
    )

    quest: Optional[Quest] = Relationship(back_populates="user_quests")

class UserAchievement(Base, table=True):

    id: Optional[int] = Field(default=None, primary_key=True)

    user_id: uuid.UUID = Field(
        sa_column=Column(UUID(as_uuid=True), ForeignKey(USER_ID), index=True, nullable=False)
    )

    achievement_id: str = Field(index=True, nullable=False)  

    progress: int = Field(default=0)  

    target: int = Field(default=1)

    is_completed: bool = Field(default=False)

    completion_date: date = Field(
        default=None,
        nullable=True
    )

    type: AchievementType = Field(
        sa_column=Column(String, nullable=False),
    )

class QuestHistory(Base, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

    user_id: uuid.UUID = Field(
        sa_column=Column(UUID(as_uuid=True), ForeignKey(USER_ID), nullable=False)
    )

    quest_id: str = Field(nullable=False)

    title: str = Field(nullable=False)
    xp_reward: int = Field(nullable=False)

    completed_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), nullable=False)
    )

class AchievementHistory(Base, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

    user_id: uuid.UUID = Field(
        sa_column=Column(UUID(as_uuid=True), ForeignKey(USER_ID), nullable=False)
    )

    achievement_id: str = Field(nullable=False)

    title: str = Field(nullable=False)
    xp_reward: int = Field(nullable=False)

    completed_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), nullable=False)
    )