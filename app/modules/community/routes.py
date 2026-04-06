from fastapi import APIRouter, Body, Depends

from app.modules.community.schemas import CommunityStats, ForumAuthor, ForumFeedRequest, ForumPostCreate, ForumPostRead, ForumTab, PostComment
from app.auth.permissions import get_current_user
from app.users.models import User


router = APIRouter(prefix="/api/v1/community", tags=["community"])


@router.get("/stats", response_model=CommunityStats)
async def get_community_stats(
    current_user: User = Depends(get_current_user),
):
    """Endpoint untuk mengambil estimasi jumlah user online"""
    raise NotImplementedError


@router.post("/feed", response_model=list[ForumPostRead])
async def get_forum_feed(
    filter: ForumFeedRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Endpoint untuk mengambil list postingan
    """
    raise NotImplementedError


# 2. Interactions (Postingan)
@router.post("/posts", response_model=ForumPostRead, status_code=201)
async def create_post(
    post: ForumPostCreate,
    current_user: User = Depends(get_current_user),
):
    """Endpoint untuk membuat post baru"""
    raise NotImplementedError


@router.post("/posts/{post_id}/comment")
async def comment_post(
    post_id: int,
    comment: PostComment,
    current_user: User = Depends(get_current_user),
):
    """Endpoint untuk mengomentari sebuah postingan"""
    raise NotImplementedError


@router.post("/posts/{post_id}/like")
async def like_post(
    post_id: int,
    current_user: User = Depends(get_current_user),
):
    """Endpoint untuk toggle tombol like (like<->dislike) sebuah post"""
    raise NotImplementedError


# 3. Ruang Belajar (Study Rooms)
@router.post("/rooms/{room_id}/join")
async def join_study_room(
    room_id: int,
    current_user: User = Depends(get_current_user),
):
    """Endpoint untuk join sebuah study room"""
    raise NotImplementedError


@router.get("/posts/{post_id}/comments", response_model=list[PostComment])
async def get_post_comments(
    post_id: int,
    current_user: User = Depends(get_current_user),
):
    """Endpoint untuk mengambil list komentar sebuah posting"""
    raise NotImplementedError