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
    username: Optional[str]
    full_name: Optional[str]
    description: Optional[str] = None
    phone_number: Optional[str]
    nim: Optional[str]
    birth_date: Optional[date]
    notifications: Optional[bool]
    share_leaderboard_stats: Optional[bool]
    total_xp: Optional[int]
    current_level: Optional[int]

class ProfileUpdate(BaseModel):
    username: Optional[str] = None
    full_name: Optional[str] = None
    description: Optional[str] = None
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
    username: str
    full_name: str

class FriendUserView(PublicUserView):
    level: int
    total_xp: int
    online_status: int