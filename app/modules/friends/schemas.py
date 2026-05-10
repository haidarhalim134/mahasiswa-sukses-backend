from datetime import datetime
from enum import Enum
from typing import Optional, List
from pydantic import BaseModel, Field, field_validator
from app.users.schemas import PublicUserView

class FriendshipStatus(str, Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"

class FriendRead(PublicUserView):
    level: int
    total_xp: int

class FriendRequest(BaseModel):
    username_or_email: str