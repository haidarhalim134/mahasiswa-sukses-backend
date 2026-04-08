from typing import Optional
from datetime import datetime
from enum import Enum
import uuid

from app.db.base import Base
from sqlmodel import ForeignKey, SQLModel, Field, UUID
from sqlalchemy import Column, String, DateTime, Boolean

from app.modules.progress_tracking.schemas import TaskCategory, TaskPriority, TaskProgress


class Task(Base, table=True):

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: uuid.UUID = Field(
        sa_column=Column(UUID(as_uuid=True), ForeignKey("users.id"), index=True, nullable=False)
    )

    title: str = Field(sa_column=Column(String, nullable=False))
    description: Optional[str] = Field(default=None, sa_column=Column(String))

    category: TaskCategory = Field(
        sa_column=Column(String, nullable=False)
    )

    priority: TaskPriority = Field(
        sa_column=Column(String, nullable=False)
    )

    progress: TaskProgress = Field(
        default=TaskProgress.TODO,
        sa_column=Column(String, nullable=False, server_default="Todo")
    )

    is_completed: bool = Field(
        default=False,
        sa_column=Column(Boolean, nullable=False, server_default="false")
    )

    deadline: datetime = Field(
        sa_column=Column(DateTime(timezone=True), nullable=False)
    )
