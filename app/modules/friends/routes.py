from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.auth.permissions import get_current_user
from app.db.session import get_db
from app.users.models import User
from app.modules.friends.schemas import FriendRead, FriendRequest, FriendSummary
from app.users.schemas import PublicUserView

router = APIRouter(prefix="/friends", tags=["friends"])

@router.get("/", response_model=list[FriendRead])
async def list_friends(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Endpoint untuk mengambil list teman"""
    raise NotImplementedError

@router.get("/summary", response_model=FriendSummary)
async def friend_summary(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Endpoint untuk mengambil stats pertemanan"""
    raise NotImplementedError

@router.post("/request")
async def add_friend(
    username_or_email: FriendRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Endpoint untuk mengirim permintaan pertemanan"""
    raise NotImplementedError

@router.get("/request_list", response_model=list[PublicUserView])
async def list_friends_request(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Endpoint untuk mengambil list permintaan pertemanan"""
    raise NotImplementedError


@router.post("/accept/{requester_id}")
async def accept_friend(
    requester_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Endpoint untuk menyetujui permintaan pertemanan"""
    raise NotImplementedError

@router.post("/deny/{requester_id}")
async def deny_friend(
    requester_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Endpoint untuk menolak permintaan pertemanan"""
    raise NotImplementedError

@router.delete("/{friend_id}")
async def remove_friend(
    friend_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Endpoint untuk menghapus teman"""
    raise NotImplementedError