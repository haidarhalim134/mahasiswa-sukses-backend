from typing import List
import enum
import uuid
from datetime import date

from sqlalchemy import String, Enum, Date
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from app.db.base import Base


class Role(str, enum.Enum):
    student = "student"
    admin = "admin"


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        index=True
    )

    email: Mapped[str] = mapped_column(
        String,
        unique=True,
        index=True,
        nullable=False,
    )

    role: Mapped[Role] = mapped_column(
        Enum(Role, native_enum=False),
        default=Role.student,
        nullable=False,
    )

    phone_number: Mapped[str] = mapped_column(
        String,
        nullable=True,
    )

    nim: Mapped[str] = mapped_column(
        String,
        unique=True,
        index=True,
        nullable=True,
    )

    full_name: Mapped[str] = mapped_column(
        String,
        nullable=True,
    )

    birth_date: Mapped[date] = mapped_column(
        Date,
        nullable=True,
    )