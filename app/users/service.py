from typing import Any


from uuid import UUID
from datetime import date, datetime, timedelta, timezone

from fastapi import HTTPException
from sqlmodel import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.supabase import get_supabase, supabase
from app.users.models import User
from app.users.schemas import FriendUserView, ProfileUpdate, PublicUserView, SettingsUpdate, UserProfile


async def create_user_profile(
    db: AsyncSession,
    user_id: UUID,
    email: str,
    phone_number: str,
    nim: str,
    username: str,
    full_name: str,
    birth_date: date,
):
    user = User(
        id=user_id,
        email=email,
        phone_number=phone_number,
        nim=nim,
        user_name=username,
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

async def get_user_by_username(
    db: AsyncSession,
    username: str
):
    stmt = select(User).where(User.user_name == username)

    result = await db.execute(stmt)

    return result.scalar_one_or_none()

def user_to_public_view(user: User):
    return PublicUserView(
        id=user.id,
        username=user.user_name,
        full_name=user.full_name,
        role=user.role
    )

def user_to_friend_view(user: User):
    return FriendUserView(
        id=user.id,
        username=user.user_name,
        full_name=user.full_name,
        level=user.level,
        total_xp=user.total_xp,
        online_status=user.is_online,
        role=user.role
    )

def user_to_private_view(user: User):
    return UserProfile(
        id=user.id,
        email=user.email,
        username=user.user_name,
        full_name=user.full_name,
        description=user.description,
        phone_number=user.phone_number,
        nim=user.nim,
        birth_date=user.birth_date,
        notifications=user.notification_on,
        share_leaderboard_stats=user.share_leaderboard_stats,
        total_xp=user.total_xp,
        current_level=user.level
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

def get_online_users_count_stmt(
    window_minutes: int = 10,
):
    threshold = datetime.now(timezone.utc) - timedelta(minutes=window_minutes)
    
    return select(func.count()).where(
        User.last_seen_at != None,
        User.last_seen_at > threshold
    )

async def get_online_users_count(
    db: AsyncSession,
    window_minutes: int = 10,
) -> int:
    result = await db.scalar(get_online_users_count_stmt(window_minutes))

    return result or 0

async def update_profile_data(
    db: AsyncSession, 
    user: User, 
    data: ProfileUpdate
) -> UserProfile:
    if data.email:
        email_used = await get_user_by_email(db, data.email)
        if email_used and email_used.id != user.id:
            raise HTTPException(
                status_code=409,
                detail="Email already used"
        )
    
    if data.username:
        username_used = await get_user_by_username(db, data.username)
        if username_used and username_used.id != user.id:
            raise HTTPException(
                status_code=409,
                detail="Username already used"
        )

    auth_updates = {}
    if data.email and data.email != user.email:
        auth_updates["email"] = data.email
    if data.password:
        auth_updates["password"] = data.password

    if auth_updates:
        # NOTE: supabase cleanup
        get_supabase().auth.admin.update_user_by_id(str(user.id), auth_updates)

    # exclude none
    update_data = data.model_dump(exclude_unset=True)
    
    # remove password, handled by supabase
    update_data.pop("password", None)

    # NOTE: inconsistencies, might rather rename user_name to username
    if data.username:
        user.user_name = data.username
        update_data.pop("username", None)

    for key, value in update_data.items():
        setattr(user, key, value)

    db.add(user)
    await db.commit()
    await db.refresh(user)
    
    return user_to_private_view(user)

async def update_user_setting(
        db: AsyncSession, 
        user_id: UUID,
        data: SettingsUpdate
    ):

    if data.notifications != None:
        await db.execute(
            update(User)
            .where(User.id == user_id)
            .values(
                notification_on=data.notifications
            )
        )

    if data.share_leaderboard_stats != None:
        await db.execute(
            update(User)
            .where(User.id == user_id)
            .values(
                share_leaderboard_stats=data.share_leaderboard_stats
            )
        )
        
    await db.commit()

async def add_xp(
    db: AsyncSession,
    user: User,
    amount: int,
):
    user.total_xp += amount

    await db.commit()