from datetime import datetime
from enum import Enum
from typing import Optional, List
from pydantic import BaseModel, Field, field_validator
from app.users.schemas import PublicUserView

class ForumTab(str, Enum):
    POSTINGAN = "postingan"
    RUANG_BELAJAR = "ruang_belajar"

class CommentCreate(BaseModel):
    comment: str = Field(..., min_length=1, max_length=500)

class CommentRead(BaseModel):
    id: int
    author: PublicUserView
    comment: str
    created_at: datetime

class ForumPostBase(BaseModel):
    title: str
    content: str
    tags: List[str] = []

    @field_validator("tags")
    def validate_tags_no_comma(cls, tags: List[str]) -> List[str]:
        for tag in tags:
            if "," in tag:
                raise ValueError("Tags must not contain commas")
        return tags

class ForumPostCreate(ForumPostBase):
    pass

class ForumPostRead(ForumPostBase):
    id: int
    author: PublicUserView
    created_at: datetime
    likes_count: int
    comments_count: int
    is_liked: bool = False 

class LikeToggleResponse(BaseModel):
    likes_count: int
    is_liked: bool

class CommunityStats(BaseModel):
    online_count: int
    active_rooms_count: int

class ForumFeedParams(BaseModel):
    tag: Optional[str] = None
    limit: int = Field(20, ge=1, le=100)
    offset: int = Field(0, ge=0)


class ChatMessageCreate(BaseModel):
    content: str = Field(..., min_length=1, max_length=1000)

class ChatMessageRead(BaseModel):
    id: int
    room_id: int
    author: PublicUserView
    content: str
    created_at: datetime

class StudyRoomRead(BaseModel):
    id: int
    title: str
    description: str
    author: PublicUserView
    current_participants: int
    max_participants: int
    is_joined: bool = False
    is_active: bool = True
    created_at: datetime