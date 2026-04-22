from typing import Optional
from datetime import datetime
import uuid

from app.db.base import Base
from sqlmodel import Field, Relationship
from sqlalchemy import Column, String, DateTime, Boolean, Integer
from sqlmodel import ForeignKey, UUID

from app.users.models import User


class ForumPost(Base, table=True):
    __tablename__ = "forum_posts"

    id: Optional[int] = Field(default=None, primary_key=True)

    author_id: uuid.UUID = Field(
        sa_column=Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    )
    author: User = Relationship(
        sa_relationship_kwargs={"foreign_keys": "[ForumPost.author_id]"}
    )

    title: str = Field(sa_column=Column(String, nullable=False))
    content: str = Field(sa_column=Column(String, nullable=False))

    # simple comma-separated tags
    tags: Optional[str] = Field(default="", sa_column=Column(String))

    created_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), nullable=False)
    )


class Comment(Base, table=True):
    __tablename__ = "forum_comments"

    id: Optional[int] = Field(default=None, primary_key=True)

    post_id: int = Field(
        sa_column=Column(Integer, ForeignKey("forum_posts.id"), nullable=False, index=True)
    )

    author_id: uuid.UUID = Field(
        sa_column=Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    )
    author: User = Relationship(
        sa_relationship_kwargs={"foreign_keys": "[Comment.author_id]"}
    )


    comment: str = Field(sa_column=Column(String, nullable=False))

    created_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), nullable=False)
    )


class PostLike(Base, table=True):
    __tablename__ = "forum_post_likes"

    post_id: int = Field(
        sa_column=Column(Integer, ForeignKey("forum_posts.id"), primary_key=True, nullable=False, index=True)
    )

    user_id: uuid.UUID = Field(
        sa_column=Column(UUID(as_uuid=True), ForeignKey("users.id"), primary_key=True, nullable=False)
    )


class StudyRoom(Base, table=True):
    __tablename__ = "study_rooms"

    id: Optional[int] = Field(default=None, primary_key=True)

    title: str = Field(sa_column=Column(String, nullable=False))
    description: str = Field(sa_column=Column(String, nullable=False))

    author_id: uuid.UUID = Field(
        sa_column=Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    )
    author: User = Relationship(
        sa_relationship_kwargs={"foreign_keys": "[StudyRoom.author_id]"}
    )

    max_participants: int = Field(
        default=20,
        sa_column=Column(Integer, nullable=False)
    )

    is_active: bool = Field(
        default=True,
        sa_column=Column(Boolean, nullable=False, server_default="true")
    )

    created_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), nullable=False)
    )


class StudyRoomParticipant(Base, table=True):
    __tablename__ = "study_room_participants"

    room_id: int = Field(
        sa_column=Column(Integer, ForeignKey("study_rooms.id"), primary_key=True, nullable=False)
    )

    user_id: uuid.UUID = Field(
        sa_column=Column(UUID(as_uuid=True), ForeignKey("users.id"), primary_key=True, nullable=False)
    )

class StudyRoomLike(Base, table=True):
    __tablename__ = "study_room_likes"

    room_id: int = Field(
        sa_column=Column(Integer, ForeignKey("study_rooms.id"), primary_key=True, nullable=False, index=True)
    )

    user_id: uuid.UUID = Field(
        sa_column=Column(UUID(as_uuid=True), ForeignKey("users.id"), primary_key=True, nullable=False)
    )


class ChatMessage(Base, table=True):
    __tablename__ = "study_room_messages"

    id: Optional[int] = Field(default=None, primary_key=True)

    room_id: int = Field(
        sa_column=Column(Integer, ForeignKey("study_rooms.id"), nullable=False, index=True)
    )

    author_id: uuid.UUID = Field(
        sa_column=Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    )
    author: User = Relationship(
        sa_relationship_kwargs={"foreign_keys": "[ChatMessage.author_id]"}
    )

    content: str = Field(sa_column=Column(String, nullable=False))

    created_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), nullable=False)
    )