from typing import Annotated
from uuid import UUID
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.permissions import get_current_user, get_current_user_id
from app.db.session import get_db
from app.modules.community import services
from app.modules.community.models import ForumPost
from app.modules.community.schemas import (
    ChatMessageCreate, ChatMessageRead,
    CommentCreate, CommentRead,
    CommunityStats, ForumCategory,
    ForumFeedParams,
    ForumPostCreate, ForumPostRead,
    LikeToggleResponse, StudyRoomCreate, StudyRoomRead
)
from app.modules.gamification.schemas import QuestEvent
from app.modules.gamification.services import progress_achievement, progress_quest
from app.users.models import User


router = APIRouter(prefix="/api/v1/community", tags=["community"])


## stats
@router.get("/stats", response_model=CommunityStats)
async def get_community_stats(
    current_user_id: Annotated[UUID, Depends(get_current_user_id)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Endpoint untuk mengambil estimasi jumlah user online"""
    return await services.get_stats(db)


## posts
@router.get("/feed/forum", response_model=list[ForumPostRead])
async def get_forum_feed(
    current_user_id: Annotated[UUID, Depends(get_current_user_id)],
    db: Annotated[AsyncSession, Depends(get_db)],
    params: Annotated[ForumFeedParams, Depends()],
):
    """Endpoint untuk mengambil list postingan"""
    return await services.get_forum_feed(db, params, current_user_id)


@router.post("/posts", response_model=ForumPostRead, status_code=201)
async def create_post(
    post: ForumPostCreate,
    current_user_id: Annotated[UUID, Depends(get_current_user_id)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Endpoint untuk membuat post baru, menerima tag dalam bentuk comma separated string 'tag1,tag2,tag3' """
    return await services.create_post(db, current_user_id, post)

@router.delete("/posts/{post_id}")
async def delete_post(
    post_id: int,
    current_user_id: Annotated[UUID, Depends(get_current_user_id)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Endpoint untuk menghapus sebuah post"""
    await services.delete_post(db, current_user_id, post_id)

@router.get("/posts/{post_id}", response_model=ForumPostRead)
async def get_post_detail(
    post_id: int,
    current_user_id: Annotated[UUID, Depends(get_current_user_id)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Endpoint untuk mengambil detail lengkap satu postingan"""
    return await services.get_post(db, post_id, current_user_id)


## comments
@router.post("/posts/{post_id}/comment", response_model=CommentRead)
async def comment_on_post(
    post_id: int,
    payload: CommentCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Endpoint untuk mengomentari sebuah postingan"""
    comment =  await services.create_comment(db, current_user.id, post_id, payload)

    # NOTE: perhaps create helper function later that call both then make sure other calls are updated as well
    # hook
    await progress_quest(db, current_user, QuestEvent.POST_COMMENT)
    await progress_achievement(db, current_user, QuestEvent.POST_COMMENT)

    post: ForumPost | None = await db.get(ForumPost, post_id)
    if post and post.category == ForumCategory.BANTUAN:
        # hook
        await progress_quest(db, current_user, QuestEvent.POST_COMMENT_ON_HELP)
        await progress_achievement(db, current_user, QuestEvent.POST_COMMENT_ON_HELP)

    return comment


@router.get("/posts/{post_id}/comments", response_model=list[CommentRead])
async def get_post_comments(
    post_id: int,
    current_user_id: Annotated[UUID, Depends(get_current_user_id)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Endpoint untuk mengambil list komentar sebuah posting"""
    return await services.get_comments(db, post_id)


## like
@router.post("/posts/{post_id}/like", response_model=LikeToggleResponse)
async def toggle_post_like(
    post_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Endpoint untuk toggle tombol like (like<->dislike) sebuah post"""
    return await services.toggle_post_like(db, current_user, post_id)


## study room
@router.get("/feed/room", response_model=list[StudyRoomRead])
async def get_room_feed(
    current_user_id: Annotated[UUID, Depends(get_current_user_id)],
    db: Annotated[AsyncSession, Depends(get_db)],
    query: str | None = "",
):
    """Endpoint untuk mengambil list study room, menerima query berupa string"""
    return await services.get_room_feed(db, query, current_user_id)

@router.post("/room", response_model=StudyRoomRead, status_code=201)
async def create_room(
    room: StudyRoomCreate,
    current_user_id: Annotated[UUID, Depends(get_current_user_id)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Endpoint untuk membuat room baru"""
    return await services.create_room(db, current_user_id, room)

@router.delete("/room/{room_id}")
async def delete_room(
    room_id: int,
    current_user_id: Annotated[UUID, Depends(get_current_user_id)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Endpoint untuk menghapus sebuah room"""
    await services.delete_room(db, current_user_id, room_id)

@router.post("/room/{room_id}/like", response_model=LikeToggleResponse)
async def toggle_room_like(
    room_id: int,
    current_user_id: Annotated[UUID, Depends(get_current_user_id)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Endpoint untuk toggle tombol like (like<->dislike) sebuah study room"""
    return await services.toggle_room_like(db, current_user_id, room_id)

@router.post("/rooms/{room_id}/join", response_model=StudyRoomRead)
async def join_study_room(
    room_id: int,
    current_user_id: Annotated[UUID, Depends(get_current_user_id)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """
    Endpoint untuk join study room. 

    Setelah endpoint ini mengembalikan status sukses (200 OK), silakan lakukan langkah berikut 
    menggunakan Supabase SDK untuk mengaktifkan fitur real-time:

    1. Inisialisasi Channel:
       Gunakan `supabase.channel('study_room:{room_id}')`. Pastikan nama channel unik per room.

    2. Listen Postgres Changes:
       Gunakan `.on('postgres_changes', ...)` pada table 'study_room_messages' untuk memantau secara realtime pesan yang user lain kirimkan. 

       Gunakan `.on('postgres_changes', { event: '*', table: 'room_chat_likes' }, ...)` pada table 'room_chat_likes' untuk memantau secara realtime like dan unlike.
       Update UI secara lokal berdasarkan `payload.eventType`:
       - 'INSERT': Tambah jumlah like pada chat terkait.
       - 'DELETE': Kurangi jumlah like pada chat terkait.
       Gunakan `chat_id` dari payload untuk menargetkan elemen chat tertentu untuk mengupdate jumlah like dan dislike.

       Gunakan filter: `filter: 'room_id=eq.{room_id}'` agar user tidak menerima 
       pesan dan event like dari room lain.

    3. Presence (Seat Count & Status):
       Gunakan `.on('presence', { event: 'sync' }, ...)` untuk memantau siapa saja yang online.
       Data dari presence ini yang digunakan untuk update UI "15/20 Peserta" secara dinamis.
       Jangan lupa panggil `.track()` setelah subscribe agar user terhitung online.

    4. Broadcast (Typing Indicator):
       Untuk fitur "... sedang mengetik", gunakan `.on('broadcast', { event: 'typing' }, ...)`.

    5. Auth:
       Gunakan Access Token (JWT) yang didapat saat login untuk inisialisasi Supabase client.

    contoh implementasi: https://github.com/haidarhalim134/mahasiswa-sukses-backend/blob/main/examples/study-room-sample.html
    """
    return await services.join_room(db, current_user_id, room_id)


@router.delete("/rooms/{room_id}/leave")
async def leave_study_room(
    room_id: int,
    current_user_id: Annotated[UUID, Depends(get_current_user_id)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Endpoint untuk meninggalkan study room"""
    await services.leave_room(db, current_user_id, room_id)


## chat
@router.get("/rooms/{room_id}/messages", response_model=list[ChatMessageRead])
async def get_chat_history(
    room_id: int,
    current_user_id: Annotated[UUID, Depends(get_current_user_id)],
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    before_id: int | None = None,
):
    """
    Endpoint untuk mengambil chat history terbaru, panggil saat pertama kali join room.
    """
    return await services.get_messages(db, current_user_id, room_id, limit, before_id)


@router.post("/rooms/{room_id}/messages", response_model=ChatMessageRead)
async def send_chat_message(
    room_id: int,
    payload: ChatMessageCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """
    Endpoint untuk mengirim pesan ke study room, set replying_to = id chat lain di study room yang sama untuk me-reply.
    """
    return await services.send_message(db, current_user, room_id, payload)

@router.post("/room/message/{room_message_id}/like", response_model=LikeToggleResponse)
async def toggle_room_chat_like(
    room_message_id: int,
    current_user_id: Annotated[UUID, Depends(get_current_user_id)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Endpoint untuk toggle tombol like (like<->dislike) sebuah chat di dalam study room."""
    return await services.toggle_room_chat_like(db, current_user_id, room_message_id)