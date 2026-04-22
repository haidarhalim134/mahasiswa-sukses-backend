from typing import Optional
from datetime import datetime, timezone
from enum import Enum
import uuid

from app.db.base import Base
from sqlmodel import ForeignKey, Integer, Relationship, SQLModel, Field, UUID, Text, func
from sqlalchemy import Column, String, DateTime, Boolean

from app.modules.progress_tracking.schemas import TaskCategory, TaskPriority, TaskProgress
from app.modules.quiz.schemas import QuizDifficulty, QuizOption, QuizStatus
from app.users.models import User

from datetime import datetime, timedelta, timezone
from typing import Optional
import uuid

from sqlmodel import Field, Relationship
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey
from sqlalchemy.sql import func

class Quiz(Base, table=True):
    __tablename__ = "quizzes"

    id: Optional[int] = Field(default=None, primary_key=True)
    title: str = Field(sa_column=Column(String, nullable=False, index=True))
    category: str = Field(sa_column=Column(String, nullable=False, index=True))
    duration_minutes: int = Field(sa_column=Column(Integer, nullable=False))
    minimum_score: int = Field(sa_column=Column(Integer, nullable=False, default=0))
    xp_reward: int = Field(sa_column=Column(Integer, nullable=False, default=0))
    difficulty: QuizDifficulty = Field(sa_column=Column(String, nullable=False))
    is_active: bool = Field(sa_column=Column(Boolean, nullable=False, default=True))
    created_at: datetime = Field(
        default_factory=lambda : datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), nullable=False, server_default=func.now()),
    )

    questions: list["QuizQuestion"] = Relationship(
        back_populates="quiz",
        sa_relationship_kwargs={
            "primaryjoin": "Quiz.id == QuizQuestion.quiz_id",
        },
    )


class QuizQuestion(Base, table=True):
    __tablename__ = "quiz_questions"

    id: Optional[int] = Field(default=None, primary_key=True)
    quiz_id: int = Field(
        sa_column=Column(Integer, ForeignKey("quizzes.id", ondelete="CASCADE"), nullable=False, index=True)
    )
    quiz: Quiz = Relationship(
        sa_relationship_kwargs={"foreign_keys": "[QuizQuestion.quiz_id]"}
    )

    order_index: int = Field(sa_column=Column(Integer, nullable=False, index=True))
    text: str = Field(sa_column=Column(Text, nullable=False))

    option_a: str = Field(sa_column=Column(Text, nullable=False))
    option_b: str = Field(sa_column=Column(Text, nullable=False))
    option_c: str = Field(sa_column=Column(Text, nullable=False))
    option_d: str = Field(sa_column=Column(Text, nullable=False))

    correct_option: QuizOption = Field(
        sa_column=Column(String, nullable=False)
    )


class QuizAttempt(Base, table=True):
    __tablename__ = "quiz_attempts"

    id: Optional[int] = Field(default=None, primary_key=True)

    quiz_id: int = Field(
        sa_column=Column(Integer, ForeignKey("quizzes.id", ondelete="CASCADE"), nullable=False, index=True)
    )
    quiz: "Quiz" = Relationship(
        sa_relationship_kwargs={"foreign_keys": "[QuizAttempt.quiz_id]"}
    )

    user_id: uuid.UUID = Field(
        sa_column=Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    )
    user: "User" = Relationship(
        sa_relationship_kwargs={"foreign_keys": "[QuizAttempt.user_id]"}
    )

    # TODO: might no longer be necessary
    status: QuizStatus = Field(
        sa_column=Column(String, nullable=False, default=QuizStatus.BERJALAN.value)
    )

    started_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), nullable=False, server_default=func.now()),
    )

    # should only be filled when user submitted, else None
    submitted_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), nullable=True),
    )

    # should only be filled when user exited, else None
    exited_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), nullable=True),
    )

    correct_answers: int = Field(sa_column=Column(Integer, nullable=False, default=0))
    total_questions: int = Field(sa_column=Column(Integer, nullable=False, default=0))
    minimum_score: int = Field(sa_column=Column(Integer, nullable=False, default=0))
    passed: bool = Field(sa_column=Column(Boolean, nullable=False, default=False))
    points_gained: int = Field(sa_column=Column(Integer, nullable=False, default=0))
    streak_bonus: int = Field(sa_column=Column(Integer, nullable=False, default=0))

    certificate_id: Optional[str] = Field(
        default=None,
        sa_column=Column(String, nullable=True, index=True),
    )

    answers: list["QuizAttemptAnswer"] = Relationship(
        back_populates="attempt",
        sa_relationship_kwargs={
            "primaryjoin": "QuizAttempt.id == QuizAttemptAnswer.attempt_id",
        },
    )

    @property
    def end_time(self) -> datetime:
        return self.started_at + timedelta(minutes=self.quiz.duration_minutes)

    @property
    def is_expired(self) -> bool:
        return datetime.now(timezone.utc) > self.end_time

    @property
    def computed_status(self) -> QuizStatus:
        """
        Dynamic status without relying on scheduler
        """
        if self.exited_at:
            return QuizStatus.BATAL

        if self.submitted_at:
            return QuizStatus.SELESAI

        if self.is_expired:
            return QuizStatus.SELESAI

        return QuizStatus.BERJALAN


class QuizAttemptAnswer(Base, table=True):
    __tablename__ = "quiz_attempt_answers"

    id: Optional[int] = Field(default=None, primary_key=True)
    attempt_id: int = Field(
        sa_column=Column(Integer, ForeignKey("quiz_attempts.id", ondelete="CASCADE"), nullable=False, index=True)
    )
    attempt: QuizAttempt = Relationship(back_populates="answers")

    question_id: int = Field(
        sa_column=Column(Integer, ForeignKey("quiz_questions.id", ondelete="CASCADE"), nullable=False, index=True)
    )
    selected_option: QuizOption = Field(
        sa_column=Column(String, nullable=False)
    )
    is_correct: bool = Field(sa_column=Column(Boolean, nullable=False, default=False))
