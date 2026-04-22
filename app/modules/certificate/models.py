from typing import Optional
from datetime import datetime, timezone
import uuid

from app.db.base import Base
from sqlmodel import Field, Relationship
from sqlalchemy import Column, String, DateTime, Boolean, Integer
from sqlmodel import ForeignKey, UUID

from app.modules.certificate.schemas import CertificateSource
from app.users.models import User


class Certificate(Base, table=True):
    __tablename__ = "certificates"

    id: Optional[str] = Field(default_factory=uuid.uuid4, primary_key=True)

    user_id: uuid.UUID = Field(
        sa_column=Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    )
    user: User = Relationship(
        sa_relationship_kwargs={"foreign_keys": "[Certificate.user_id]"}
    )

    source: CertificateSource = Field(
        sa_column=Column(String, nullable=False)
    )
    source_id: int = Field(nullable=False)

    title: str = Field(nullable=False)
    category: str = Field(nullable=False)

    issued_at: datetime = Field(
        default_factory=lambda : datetime.now(timezone.utc),
        sa_column=Column(
            DateTime(timezone=True),
            nullable=True
        )
    )
