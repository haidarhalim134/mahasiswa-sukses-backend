from datetime import datetime, date
from typing import Optional
import uuid

from app.db.base import Base
from sqlmodel import DateTime, Field, Column, Relationship
from sqlalchemy import String, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID

from app.modules.gamification.schemas import QuestFrequency, AchievementType


class UserQuest(Base, table=True):
    """
    Stores per-user quest progress
    """

    id: Optional[int] = Field(default=None, primary_key=True)

    user_id: uuid.UUID = Field(
        sa_column=Column(UUID(as_uuid=True), ForeignKey("users.id"), index=True, nullable=False)
    )

    quest_id: str = Field(index=True, nullable=False)  

    progress: int = Field(default=0)  

    target: int = Field(default=1)

    is_completed: bool = Field(default=False)

    frequency: QuestFrequency = Field(
        sa_column=Column(String, nullable=False),
    )

class UserAchievement(Base, table=True):
    """
    Stores per-user achievement progress
    """

    id: Optional[int] = Field(default=None, primary_key=True)

    user_id: uuid.UUID = Field(
        sa_column=Column(UUID(as_uuid=True), ForeignKey("users.id"), index=True, nullable=False)
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
