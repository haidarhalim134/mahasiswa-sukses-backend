from datetime import date
import re
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.users.models import Role

class UserStats(BaseModel):
    total_points: int
    ranking: int
    streak_days: int
    completion_percentage: float

class UserProfile(BaseModel):
    id: UUID
    email: str
    username: Optional[str] = None
    full_name: Optional[str] = None
    description: Optional[str] = None
    phone_number: Optional[str] = None
    nim: Optional[str] = None
    birth_date: Optional[date] = None
    notifications: Optional[bool] = None
    share_leaderboard_stats: Optional[bool] = None
    total_xp: Optional[int] = None
    current_level: Optional[int] = None
    role: Role = Role.student

class ProfileUpdate(BaseModel):
    username: Optional[str] = None
    full_name: Optional[str] = None
    description: Optional[str] = None
    email: Optional[EmailStr] = None
    phone_number: Optional[str] = None
    nim: Optional[str] = None
    birth_date: Optional[date] = None
    password: Optional[str] = Field(None, min_length=8)

    @field_validator("password")
    def validate_password_complexity(cls, v):
        # at least one letter: (?=.*[A-Za-z])
        # at least one digit: (?=.*\d)
        # at least one special character: (?=.*[@$!%*#?&])
        # at least 8 char long: {8,}
        pattern = r"^(?=.*[A-Za-z])(?=.*\d)(?=.*[@$!%*#?&])[A-Za-z\d@$!%*#?&]{8,}$"
        
        if v != None and not re.match(pattern, v):
            raise ValueError(
                "Password must contain at least one letter, one number, and one special character"
            )
        return v

class SettingsUpdate(BaseModel):
    notifications: Optional[bool] = None
    share_leaderboard_stats: Optional[bool] = None

class PublicUserView(BaseModel):
    id: UUID
    username: str
    full_name: str
    role: Role

class FriendUserView(PublicUserView):
    level: int
    total_xp: int
    online_status: bool