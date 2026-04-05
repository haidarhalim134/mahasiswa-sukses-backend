
from fastapi import APIRouter, Body

from app.modules.community.schemas import CommunityStats, ForumFeedRequest, ForumPostCreate, ForumPostRead, ForumTab, PostComment


router = APIRouter(prefix="/api/v1/community", tags=["community"])

@router.get("/stats", response_model=CommunityStats)
async def get_community_stats():
    """Endpoint untuk mengambil estimasi jumlah user online"""
    raise NotImplementedError

@router.post("/feed", response_model=list[ForumPostRead])
async def get_forum_feed(filter: ForumFeedRequest):
    """
    Endpoint untuk mengambil list postingan
    """
    raise NotImplementedError

# 2. Interactions (Postingan)
@router.post("/posts", response_model=ForumPostRead, status_code=201)
async def create_post(post: ForumPostCreate):
    """Endpoint untuk membuat post baru"""
    raise NotImplementedError

@router.post("/posts/{post_id}/comment")
async def comment_post(post_id: int, comment: PostComment):
    """Endpoint untuk mengomentari sebuah postingan"""
    raise NotImplementedError

@router.post("/posts/{post_id}/like")
async def like_post(post_id: int):
    """Endpoint untuk toggle tombol like (like<->dislike) sebuah post"""
    raise NotImplementedError

# 3. Ruang Belajar (Study Rooms)
@router.post("/rooms/{room_id}/join")
async def join_study_room(room_id: int):
    """Endpoint untuk join sebuah study room"""
    raise NotImplementedError

@router.get("/posts/{post_id}/comments")
async def get_post_comments(post_id: int):
    """Endpoint untuk mengambil list komentar sebuah posting"""
    raise NotImplementedError