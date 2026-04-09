from datetime import datetime
from enum import Enum
from typing import Optional, List
from pydantic import BaseModel, Field
from app.users.schemas import PublicUserView

class ForumTab(str, Enum):
    POSTINGAN = "postingan"
    RUANG_BELAJAR = "ruang belajar"

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

class StudyRoomRead(ForumPostRead):
    current_participants: int
    max_participants: int
    is_joined: bool = False

class CommunityStats(BaseModel):
    online_count: int
    active_rooms_count: int

class ForumFeedParams(BaseModel):
    tab: ForumTab = ForumTab.POSTINGAN
    tag: Optional[str] = None
    limit: int = Field(20, ge=1, le=100)
    offset: int = Field(0, ge=0)