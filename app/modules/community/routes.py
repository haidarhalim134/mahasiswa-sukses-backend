from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.permissions import get_current_user
from app.db.session import get_db
from app.modules.community import services
from app.modules.community.schemas import (
    ChatMessageCreate, ChatMessageRead,
    CommentCreate, CommentRead,
    CommunityStats,
    ForumFeedParams,
    ForumPostCreate, ForumPostRead,
    LikeToggleResponse, StudyRoomCreate, StudyRoomRead
)
from app.users.models import User


router = APIRouter(prefix="/api/v1/community", tags=["community"])


## stats
@router.get("/stats", response_model=CommunityStats)
async def get_community_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Endpoint untuk mengambil estimasi jumlah user online"""
    return await services.get_stats(db)


## posts
@router.get("/feed/forum", response_model=list[ForumPostRead])
async def get_forum_feed(
    params: ForumFeedParams = Depends(),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Endpoint untuk mengambil list postingan"""
    return await services.get_forum_feed(db, params, current_user.id)


@router.post("/posts", response_model=ForumPostRead, status_code=201)
async def create_post(
    post: ForumPostCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Endpoint untuk membuat post baru, menerima tag dalam bentuk comma separated string 'tag1,tag2,tag3' """
    return await services.create_post(db, current_user.id, post)


@router.get("/posts/{post_id}", response_model=ForumPostRead)
async def get_post_detail(
    post_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Endpoint untuk mengambil detail lengkap satu postingan"""
    return await services.get_post(db, post_id, current_user.id)


## comments
@router.post("/posts/{post_id}/comment", response_model=CommentRead)
async def comment_on_post(
    post_id: int,
    payload: CommentCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Endpoint untuk mengomentari sebuah postingan"""
    return await services.create_comment(db, current_user.id, post_id, payload)


@router.get("/posts/{post_id}/comments", response_model=list[CommentRead])
async def get_post_comments(
    post_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Endpoint untuk mengambil list komentar sebuah posting"""
    return await services.get_comments(db, post_id)


## like
@router.post("/posts/{post_id}/like", response_model=LikeToggleResponse)
async def toggle_post_like(
    post_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Endpoint untuk toggle tombol like (like<->dislike) sebuah post"""
    return await services.toggle_post_like(db, current_user.id, post_id)


## study room
@router.get("/feed/room", response_model=list[StudyRoomRead])
async def get_room_feed(
    query: str | None = "",
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Endpoint untuk mengambil list study room, menerima query berupa string"""
    return await services.get_room_feed(db, query, current_user.id)

@router.post("/room", response_model=StudyRoomRead, status_code=201)
async def create_room(
    room: StudyRoomCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Endpoint untuk membuat room baru"""
    return await services.create_room(db, current_user.id, room)

@router.post("/room/{post_id}/like", response_model=LikeToggleResponse)
async def toggle_room_like(
    room_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Endpoint untuk toggle tombol like (like<->dislike) sebuah study room"""
    return await services.toggle_room_like(db, current_user.id, room_id)

@router.post("/rooms/{room_id}/join", response_model=StudyRoomRead)
async def join_study_room(
    room_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
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
    return await services.join_room(db, current_user.id, room_id)


@router.delete("/rooms/{room_id}/leave")
async def leave_study_room(
    room_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Endpoint untuk meninggalkan study room"""
    await services.leave_room(db, current_user.id, room_id)


## chat
@router.get("/rooms/{room_id}/messages", response_model=list[ChatMessageRead])
async def get_chat_history(
    room_id: int,
    limit: int = Query(50, ge=1, le=100),
    before_id: int | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Endpoint untuk mengambil chat history terbaru, panggil saat pertama kali join room.
    """
    return await services.get_messages(db, current_user.id, room_id, limit, before_id)


@router.post("/rooms/{room_id}/messages", response_model=ChatMessageRead)
async def send_chat_message(
    room_id: int,
    payload: ChatMessageCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Endpoint untuk mengirim pesan ke study room.
    """
    return await services.send_message(db, current_user, room_id, payload)