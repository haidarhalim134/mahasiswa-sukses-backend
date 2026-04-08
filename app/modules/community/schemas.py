from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel

from app.users.schemas import PublicUserView


class ForumTab(str, Enum):
    POSTINGAN = "Postingan"
    RUANG_BELAJAR = "Ruang Belajar"


class ForumPostBase(BaseModel):
    title: str
    content: str
    tags: list[str]

class ForumPostCreate(ForumPostBase):
    pass


class ForumPostRead(ForumPostBase):
    id: int
    author: PublicUserView
    created_at: datetime
    likes_count: int
    comments_count: int


class StudyRoomRead(ForumPostRead):
    current_participants: int
    max_participants: int
    is_joined: bool = False


class CommunityStats(BaseModel):
    online_count: int


class ForumFeedRequest(BaseModel):
    tab: ForumTab = ForumTab.POSTINGAN
    tag: Optional[list[str]] = None


class PostComment(BaseModel):
    author: PublicUserView
    comment: str