from uuid import UUID
from datetime import date

from sqlmodel import select
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

def user_to_public_view(user: User):
    return PublicUserView(
        id=user.id,
        full_name=user.full_name
    )