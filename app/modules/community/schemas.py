
from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel


class ForumTab(str, Enum):
    POSTINGAN = "Postingan"
    RUANG_BELAJAR = "Ruang Belajar"


class ForumAuthor(BaseModel):
    name: str
    initials: str  # e.g., "AP" or "MA"
    avatar_url: Optional[str] = None

class ForumPostBase(BaseModel):
    content: str
    tags: list[str]

class ForumPostCreate(ForumPostBase):
    pass

class ForumPostRead(ForumPostBase):
    id: int
    author: ForumAuthor
    created_at: datetime  # e.g., "2 jam yang lalu"
    likes_count: int
    comments_count: int

class StudyRoomRead(ForumPostRead):
    title: str
    current_participants: int
    max_participants: int
    is_joined: bool = False

class CommunityStats(BaseModel):
    online_count: int