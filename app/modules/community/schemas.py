from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel


class ForumTab(str, Enum):
    POSTINGAN = "Postingan"
    RUANG_BELAJAR = "Ruang Belajar"


class ForumAuthor(BaseModel):
    name: str
    avatar_url: Optional[str] = None

    model_config = {
        "json_schema_extra": {
            "example": {
                "name": "John Doe",
                "avatar_url": "https://ui-avatars.com/api/?name=John+Doe"
            }
        }
    }


class ForumPostBase(BaseModel):
    title: str
    content: str
    tags: list[str]

    model_config = {
        "json_schema_extra": {
            "example": {
                "title": "Belajar FastAPI",
                "content": "Ini adalah isi postingan",
                "tags": ["fastapi", "python"]
            }
        }
    }


class ForumPostCreate(ForumPostBase):
    pass


class ForumPostRead(ForumPostBase):
    id: int
    author: ForumAuthor
    created_at: datetime
    likes_count: int
    comments_count: int

    model_config = {
        "json_schema_extra": {
            "example": {
                "id": 1,
                "title": "Belajar FastAPI",
                "content": "Ini adalah isi postingan",
                "tags": ["fastapi", "python"],
                "author": {
                    "name": "John Doe",
                    "avatar_url": "https://ui-avatars.com/api/?name=John+Doe"
                },
                "created_at": "2024-01-01T10:00:00Z",
                "likes_count": 10,
                "comments_count": 5
            }
        }
    }


class StudyRoomRead(ForumPostRead):
    current_participants: int
    max_participants: int
    is_joined: bool = False

    model_config = {
        "json_schema_extra": {
            "example": {
                "id": 2,
                "title": "Belajar Bareng Python",
                "content": "Diskusi tentang async",
                "tags": ["python", "async"],
                "author": {
                    "name": "Jane Doe",
                    "avatar_url": None
                },
                "created_at": "2024-01-01T10:00:00Z",
                "likes_count": 3,
                "comments_count": 1,
                "current_participants": 5,
                "max_participants": 10,
                "is_joined": True
            }
        }
    }


class CommunityStats(BaseModel):
    online_count: int

    model_config = {
        "json_schema_extra": {
            "example": {
                "online_count": 120
            }
        }
    }


class ForumFeedRequest(BaseModel):
    tab: ForumTab = ForumTab.POSTINGAN
    tag: Optional[list[str]] = None

    model_config = {
        "json_schema_extra": {
            "example": {
                "tab": "Postingan",
                "tag": ["python", "fastapi"]
            }
        }
    }


class PostComment(BaseModel):
    author: ForumAuthor
    comment: str

    model_config = {
        "json_schema_extra": {
            "example": {
                "author": {
                    "name": "Jane Doe",
                    "avatar_url": None
                },
                "comment": "Nice post!"
            }
        }
    }