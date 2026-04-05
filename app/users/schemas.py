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

class ProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = Field(None, min_length=8)
    confirm_password: Optional[str] = None