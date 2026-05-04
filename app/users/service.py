from typing import Any


from uuid import UUID
from datetime import date, datetime, timedelta, timezone

from sqlmodel import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.users.models import User
from app.users.schemas import PublicUserView


async def create_user_profile(
    db: AsyncSession,
    user_id: UUID,
    email: str,
    phone_number: str,
    nim: str,
    full_name: str,
    birth_date: date,
):
    user = User(
        id=user_id,
        email=email,
        phone_number=phone_number,
        nim=nim,
        full_name=full_name,
        birth_date=birth_date,
    )

    db.add(user)

    await db.commit()
    await db.refresh(user)

    return user

async def get_user_by_id(
    db: AsyncSession,
    user_id: UUID
):
    stmt = select(User).where(User.id == user_id)

    result = await db.execute(stmt)

    return result.scalar_one_or_none()

async def get_user_by_email(
    db: AsyncSession,
    email: str
):
    stmt = select(User).where(User.email == email)

    result = await db.execute(stmt)

    return result.scalar_one_or_none()

def user_to_public_view(user: User):
    return PublicUserView(
        id=user.id,
        full_name=user.full_name
    )

async def update_last_seen(
    db: AsyncSession,
    user_id,
) -> None:
    await db.execute(
        update(User)
        .where(User.id == user_id)
        .values(last_seen_at=datetime.now(timezone.utc))
    )
    await db.commit()

async def get_online_users_count(
    db: AsyncSession,
    window_minutes: int = 10,
) -> int:
    threshold = datetime.now(timezone.utc) - timedelta(minutes=window_minutes)

    result = await db.scalar(
        select(func.count()).where(
            User.last_seen_at != None,
            User.last_seen_at > threshold
        )
    )

    return result or 0