import math
import uuid
from datetime import date, datetime
from typing import Optional
from enum import Enum

from sqlalchemy import Column, String, Integer, DateTime
from sqlmodel import Field

from app.db.base import Base


class Role(str, Enum):
    student = "student"
    admin = "admin"


class User(Base, table=True):
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
        sa_column=Column(
            String,
            nullable=False,
            server_default="student"
        )
    )

    phone_number: str = Field(
        default=None,
        nullable=True
    )

    nim: Optional[str] = Field(
        default=None,
        unique=True,
        nullable=True
    )

    full_name: str = Field(
        default=None,
        nullable=True,
    )

    birth_date: Optional[date] = Field(
        default=None,
        nullable=True,
    )

    total_xp: int = Field(
        default=0, 
        sa_column=Column(
            Integer,
            nullable=False,
            server_default="0"
        )
    )

    last_seen_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(
            DateTime(timezone=True),
            nullable=True
        )
    )

    last_login_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(
            DateTime(timezone=True),
            nullable=True
        )
    )

    current_streak: int = Field(
        default=0,
        sa_column=Column(
            Integer,
            nullable=False,
            server_default="0"
        )
    )

    longest_streak: int = Field(
        default=0,
        sa_column=Column(
            Integer,
            nullable=False,
            server_default="0"
        )
    )

    notification_on: Optional[bool] = Field(
        default=False,
        nullable=False,
    )

    @property
    def level(self):
        xp_coeff = 150 
        if self.total_xp <= 0:
            return 1
        
        calculated_lvl = math.sqrt(self.total_xp / xp_coeff) + 1
        return math.floor(calculated_lvl)