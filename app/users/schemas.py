from typing import Optional
from pydantic import BaseModel, EmailStr, Field

class UserStats(BaseModel):
    total_points: int
    ranking: int
    streak_days: int
    completion_percentage: float

class UserProfile(BaseModel):
    full_name: str
    email: EmailStr
    avatar_url: Optional[str] = None

class ProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = Field(None, min_length=8)
    confirm_password: Optional[str] = None