import uuid
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import Column, DateTime, String, UniqueConstraint, ForeignKey
from sqlmodel import Field, Index, SQLModel, UUID, func, text
from app.db.base import Base
from app.modules.friends.schemas import FriendshipStatus

class Friendship(Base, table=True):
    __tablename__ = "friendships"

    id: Optional[int] = Field(default=None, primary_key=True)
    
    requester_id: uuid.UUID = Field(
        sa_column=Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    )
    
    requested_id: uuid.UUID = Field(
        sa_column=Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    )
    
    status: FriendshipStatus = Field(
        default=FriendshipStatus.PENDING,
        sa_column=Column(String, nullable=False, server_default="pending")
    )
    
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), nullable=False)
    )

    # to properly enforce uniqueness when requester_id and requested_id can be flupped and should be treated the same
    __table_args__ = (
        Index(
            "unique_friendship_pair",
            func.least(text("requester_id"), text("requested_id")),
            func.greatest(text("requester_id"), text("requested_id")),
            unique=True,
        ),
    )