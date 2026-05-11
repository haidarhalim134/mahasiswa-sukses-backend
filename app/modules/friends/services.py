from uuid import UUID
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import or_, and_
from sqlmodel import select, delete, update, func
from fastapi import HTTPException, status

from app.users.models import User
from app.modules.friends.models import Friendship
from app.modules.friends.schemas import FriendshipStatus, FriendSummary
from app.users.service import get_user_by_email, get_user_by_username


async def get_friends_list_service(db: AsyncSession, user_id: UUID) -> List[User]:
    stmt = (
        select(User)
        .join(
            Friendship,
            or_(
                and_(Friendship.requester_id == user_id, Friendship.requested_id == User.id),
                and_(Friendship.requested_id == user_id, Friendship.requester_id == User.id)
            )
        )
        .where(Friendship.status == FriendshipStatus.ACCEPTED)
    )
    result = await db.execute(stmt)
    return result.scalars().all()

async def get_friend_summary_service(db: AsyncSession, user_id: UUID) -> dict:
    friend_count = await db.scalar(
        select(func.count(Friendship.id)).where(
            and_(
                or_(Friendship.requester_id == user_id, Friendship.requested_id == user_id),
                Friendship.status == FriendshipStatus.ACCEPTED
            )
        )
    )
    
    request_count = await db.scalar(
        select(func.count(Friendship.id)).where(
            and_(Friendship.requested_id == user_id, Friendship.status == FriendshipStatus.PENDING)
        )
    )
    
    return {
        "friend_count": friend_count or 0,
        "friend_request_count": request_count or 0
    }

async def send_friend_request_service(db: AsyncSession, requester: User, email_or_username: str):
    # try to find as email first then username
    target_user = await get_user_by_email(db, email_or_username) or await get_user_by_username(db, email_or_username)
    
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if target_user.id == requester.id:
        raise HTTPException(status_code=400, detail="You can't add yourself as a friend")

    existing = await db.scalar(
        select(Friendship).where(
            or_(
                and_(Friendship.requester_id == requester.id, Friendship.requested_id == target_user.id),
                and_(Friendship.requester_id == target_user.id, Friendship.requested_id == requester.id)
            )
        )
    )
    
    if existing:
        raise HTTPException(status_code=400, detail="Friend request already sent")

    new_request = Friendship(requester_id=requester.id, requested_id=target_user.id)
    db.add(new_request)
    await db.commit()

async def get_pending_requests_service(db: AsyncSession, user_id: UUID) -> List[User]:
    stmt = (
        select(User)
        .join(Friendship, Friendship.requester_id == User.id)
        .where(and_(Friendship.requested_id == user_id, Friendship.status == FriendshipStatus.PENDING))
    )
    result = await db.execute(stmt)
    return result.scalars().all()

async def accept_friend_request_service(db: AsyncSession, user_id: UUID, requester_id: UUID):
    stmt = update(Friendship).where(
        and_(Friendship.requester_id == requester_id, Friendship.requested_id == user_id)
    ).values(status=FriendshipStatus.ACCEPTED)
    
    result = await db.execute(stmt)
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Friend request not found")
    
    await db.commit()

async def deny_friend_request_service(db: AsyncSession, user_id: UUID, requester_id: UUID):
    stmt = delete(Friendship).where(
        and_(Friendship.requester_id == requester_id, Friendship.requested_id == user_id, Friendship.status == FriendshipStatus.PENDING)
    )
    result = await db.execute(stmt)
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Friend request not found")
    
    await db.commit()

async def remove_friend_service(db: AsyncSession, user_id: UUID, friend_id: UUID):
    stmt = delete(Friendship).where(
        or_(
            and_(Friendship.requester_id == user_id, Friendship.requested_id == friend_id),
            and_(Friendship.requester_id == friend_id, Friendship.requested_id == user_id)
        )
    )
    await db.execute(stmt)
    await db.commit()