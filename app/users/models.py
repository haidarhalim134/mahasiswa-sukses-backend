import math
import uuid
from datetime import date, datetime, timedelta, timezone
from typing import Optional
from enum import Enum

from sqlalchemy import Column, String, Integer, DateTime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import UUID, Field, ForeignKey

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

    # unique
    user_name: str = Field(
        default=None,
        unique=True,
        nullable=False
    )

    nim: Optional[str] = Field(
        default=None,
        unique=True,
        nullable=True
    )

    full_name: str = Field(
        default=None,
        nullable=False,
    )

    description: str = Field(
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

    # user preferences
    notification_on: Optional[bool] = Field(
        default=False,
        nullable=False,
    )

    share_leaderboard_stats: Optional[bool] = Field(
        default=True,
        nullable=False,
    )

    @property
    def level(self):
        if self.total_xp <= 0:
            return 1
        
        calculated_lvl = math.sqrt(self.total_xp / 100) + 1
        return math.floor(calculated_lvl)

    # total xp until next levelup
    @property
    def xp_to_next_level(self):
        current_lvl = self.level
        next_lvl = current_lvl + 1
        
        total_xp_needed_for_next = 100 * ((next_lvl - 1) ** 2)
        
        return total_xp_needed_for_next - self.total_xp

    # amount of excess extra xp achieved minus xp used for levelling until now, simply every time user level up this value will be 0 again
    @property
    def current_level_xp(self):
        if self.total_xp <= 0:
            return 0
        
        current_lvl = self.level
        xp_at_start_of_level = 100 * ((current_lvl - 1) ** 2)
        
        return self.total_xp - xp_at_start_of_level

    # amount of xp required to move from current level to next
    @property
    def xp_required_for_this_milestone(self):
        current_lvl = self.level
        xp_for_current = 100 * ((current_lvl - 1) ** 2)
        xp_for_next = 100 * (current_lvl ** 2)
        
        return xp_for_next - xp_for_current

    @property
    def is_online(self):
        # NOTE: potentialy take the online frame and move it into config file, have a look at online estimater on community module as well
        threshold = datetime.now(timezone.utc) - timedelta(minutes=10)

        if not self.last_seen_at:
            return False
        return self.last_seen_at > threshold

class UserLoginHistory(Base, table=True):

    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        primary_key=True,
        index=True
    )

    user_id: uuid.UUID = Field(
        sa_column=Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    )

    date: datetime = Field(
        default=None,
        sa_column=Column(
            DateTime(timezone=True),
            nullable=True
        )
    )