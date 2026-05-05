from datetime import date
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field

class UserStats(BaseModel):
    total_points: int
    ranking: int
    streak_days: int
    completion_percentage: float

class UserProfile(BaseModel):
    id: UUID
    email: str
    full_name: Optional[str]
    phone_number: Optional[str]
    nim: Optional[str]
    birth_date: Optional[date]
    notifications: Optional[bool]
    share_leaderboard_stats: Optional[bool]

class ProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone_number: Optional[str] = None
    nim: Optional[str] = None
    birth_date: Optional[date] = None
    password: Optional[str] = Field(None, min_length=8)

class SettingsUpdate(BaseModel):
    notifications: Optional[bool] = None
    share_leaderboard_stats: Optional[bool] = None

class PublicUserView(BaseModel):
    id: UUID
    full_name: str