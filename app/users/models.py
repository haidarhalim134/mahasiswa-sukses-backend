import uuid
from datetime import date
from typing import Optional
from enum import Enum

from sqlmodel import SQLModel, Field


class Role(str, Enum):
    student = "student"
    admin = "admin"


class User(SQLModel, table=True):
    __tablename__ = "users"

    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        primary_key=True,
        index=True
    )

    email: str = Field(
        index=True,
        unique=True,
        nullable=False
    )

    role: Role = Field(
        default=Role.student,
        nullable=False
    )

    phone_number: Optional[str] = Field(
        default=None,
        nullable=True
    )

    nim: Optional[str] = Field(
        default=None,
        index=True,
        unique=True
    )

    full_name: Optional[str] = Field(
        default=None
    )

    birth_date: Optional[date] = Field(
        default=None
    )