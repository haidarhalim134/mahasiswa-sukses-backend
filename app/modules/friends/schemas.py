from datetime import datetime
from enum import Enum
from typing import Optional, List
from pydantic import BaseModel, Field, field_validator
from app.users.schemas import PublicUserView

class FriendshipStatus(str, Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"

class FriendRequest(BaseModel):
    email_or_username: str

class FriendSummary(BaseModel):
    friend_count: int
    friend_request_count: int