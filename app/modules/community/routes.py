from fastapi import APIRouter, Depends, Query, status
from app.auth.permissions import get_current_user
from app.users.models import User
from .schemas import (
    ChatMessageCreate, ChatMessageRead, CommunityStats, ForumFeedParams, ForumPostCreate, 
    ForumPostRead, CommentRead, CommentCreate, JoinRoomResponse, LikeToggleResponse
)

router = APIRouter(prefix="/api/v1/community", tags=["community"])


@router.get("/stats", response_model=CommunityStats)
async def get_community_stats(
    current_user: User = Depends(get_current_user),
):
    """Endpoint untuk mengambil estimasi jumlah user online"""
    raise NotImplementedError


@router.get("/feed", response_model=list[ForumPostRead])
async def get_forum_feed(
    params: ForumFeedParams = Depends(),
    current_user: User = Depends(get_current_user),
):
    """Endpoint untuk mengambil list postingan"""
    raise NotImplementedError


## postingan
@router.post("/posts", response_model=ForumPostRead, status_code=201)
async def create_post(
    post: ForumPostCreate,
    current_user: User = Depends(get_current_user),
):
    """Endpoint untuk membuat post baru"""
    raise NotImplementedError


@router.get("/posts/{post_id}", response_model=ForumPostRead)
async def get_post_detail(
    post_id: int, 
    current_user: User = Depends(get_current_user)
):
    """Endpoint untuk mengambil detail lengkap satu postingan"""
    raise NotImplementedError


@router.post("/posts/{post_id}/comment", response_model=CommentRead)
async def comment_on_post(
    post_id: int,
    payload: CommentCreate,
    current_user: User = Depends(get_current_user),
):
    """Endpoint untuk mengomentari sebuah postingan"""
    raise NotImplementedError


@router.post("/posts/{post_id}/like", response_model=LikeToggleResponse)
async def toggle_post_like(
    post_id: int, 
    current_user: User = Depends(get_current_user)
):
    """Endpoint untuk toggle tombol like (like<->dislike) sebuah post"""
    raise NotImplementedError

@router.get("/posts/{post_id}/comments", response_model=list[CommentRead])
async def get_post_comments(
    post_id: int,
    current_user: User = Depends(get_current_user),
):
    """Endpoint untuk mengambil list komentar sebuah posting"""
    raise NotImplementedError


## study room
@router.post("/rooms/{room_id}/join", response_model=JoinRoomResponse)
async def join_study_room(
    room_id: int,
    current_user: User = Depends(get_current_user),
):
    """
    Endpoint untuk join study room. 

    Setelah endpoint ini mengembalikan status sukses (200 OK), silakan lakukan langkah berikut 
    menggunakan Supabase SDK untuk mengaktifkan fitur real-time:

    1. Inisialisasi Channel:
       Gunakan `supabase.channel('study_room:{room_id}')`. Pastikan nama channel unik per room.

    2. Listen Postgres Changes:
       Gunakan `.on('postgres_changes', ...)` pada table 'study_room_messages'. 
       Gunakan filter: `filter: 'room_id=eq.{room_id}'` agar user tidak menerima 
       pesan dari room lain.

    3. Presence (Seat Count & Status):
       Gunakan `.on('presence', { event: 'sync' }, ...)` untuk memantau siapa saja yang online.
       Data dari presence ini yang digunakan untuk update UI "15/20 Peserta" secara dinamis.
       Jangan lupa panggil `.track()` setelah subscribe agar user terhitung online.

    4. Broadcast (Typing Indicator):
       Untuk fitur "... sedang mengetik", gunakan `.on('broadcast', { event: 'typing' }, ...)`.

    5. Auth:
       Gunakan Access Token (JWT) yang didapat saat login untuk inisialisasi Supabase client.
    """
    raise NotImplementedError


@router.get("/rooms/{room_id}/messages", response_model=list[ChatMessageRead])
async def get_chat_history(
    room_id: int,
    limit: int = Query(50, ge=1, le=100),
    before_id: int | None = None,
    current_user: User = Depends(get_current_user),
):
    """
    Endpoint untuk mengambil chat history terbaru, panggil saat pertama kali join room.
    """
    raise NotImplementedError


@router.post("/rooms/{room_id}/messages", response_model=ChatMessageRead)
async def send_chat_message(
    room_id: int,
    payload: ChatMessageCreate,
    current_user: User = Depends(get_current_user),
):
    """
    Endpoint kirim pesan stury room.
    """
    raise NotImplementedError


@router.delete("/rooms/{room_id}/leave")
async def leave_study_room(
    room_id: int,
    current_user: User = Depends(get_current_user),
):
    """Endpoint untuk meninggalkan study room"""
    raise NotImplementedError