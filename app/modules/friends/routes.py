from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.auth.permissions import get_current_user
from app.db.session import get_db
from app.modules.friends.services import accept_friend_request_service, deny_friend_request_service, get_friend_summary_service, get_friends_list_service, get_pending_requests_service, remove_friend_service, send_friend_request_service
from app.users.models import User
from app.modules.friends.schemas import FriendRequest, FriendSummary
from app.users.schemas import FriendUserView, PublicUserView

router = APIRouter(prefix="/api/v1/friends", tags=["friends"])

@router.get("/", response_model=list[FriendUserView])
async def list_friends(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Endpoint untuk mengambil list teman"""
    return await get_friends_list_service(db, current_user.id)

@router.get("/summary", response_model=FriendSummary)
async def friend_summary(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Endpoint untuk mengambil stats pertemanan"""
    return await get_friend_summary_service(db, current_user.id)

@router.post("/request")
async def add_friend(
    payload: FriendRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Endpoint untuk mengirim permintaan pertemanan"""
    return await send_friend_request_service(db, current_user, payload.email_or_username)

@router.get("/request_list", response_model=list[FriendUserView])
async def list_friends_request(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Endpoint untuk mengambil list permintaan pertemanan (incoming)"""
    return await get_pending_requests_service(db, current_user.id)

@router.post("/accept/{requester_id}")
async def accept_friend(
    requester_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Endpoint untuk menyetujui permintaan pertemanan"""
    return await accept_friend_request_service(db, current_user.id, requester_id)

@router.post("/deny/{requester_id}")
async def deny_friend(
    requester_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Endpoint untuk menolak permintaan pertemanan"""
    return await deny_friend_request_service(db, current_user.id, requester_id)

@router.delete("/{friend_id}")
async def remove_friend(
    friend_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Endpoint untuk menghapus teman"""
    return await remove_friend_service(db, current_user.id, friend_id)