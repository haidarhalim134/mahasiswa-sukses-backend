import asyncio
from datetime import datetime
from uuid import UUID
from fastapi import HTTPException
from sqlmodel import String, cast, or_, select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.community.models import (
    ForumPost, Comment, PostLike,
    StudyRoom, StudyRoomLike, StudyRoomParticipant, ChatMessage
)
from app.modules.community.schemas import (
    CommunityStats,
    ForumFeedParams,
    ForumPostCreate,
    ForumPostRead,
    CommentRead,
    LikeToggleResponse,
    ChatMessageRead,
    StudyRoomCreate,
    StudyRoomRead
)
from app.users.schemas import PublicUserView
from app.users.service import get_user_by_id, user_to_public_view


## stats
async def get_stats(db: AsyncSession) -> CommunityStats:
    return CommunityStats(
        online_count=0,
        active_rooms_count=0
    )


## posts
async def create_post(db: AsyncSession, user_id, payload: ForumPostCreate) -> ForumPostRead:
    post = ForumPost(
        author_id=user_id,
        title=payload.title,
        content=payload.content,
        tags=",".join(payload.tags),
        category=payload.category,
        created_at=datetime.utcnow()
    )
    db.add(post)
    await db.commit()
    await db.refresh(post)

    return await _build_post_response(db, post, user_id)


async def get_post(db: AsyncSession, post_id: int, user_id: UUID) -> ForumPostRead | None:
    result = await db.execute(
        select(ForumPost).where(ForumPost.id == post_id)
    )
    post = result.scalar_one_or_none()

    if not post:
        return None

    return await _build_post_response(db, post, user_id)


async def get_forum_feed(db: AsyncSession, params: ForumFeedParams, user_id: UUID) -> list[ForumPostRead]:
    stmt = select(ForumPost).order_by(desc(ForumPost.created_at))

    if params.tag:
        stmt = stmt.where(cast(ForumPost.tags, String).contains(params.tag))

    stmt = stmt.offset(params.offset).limit(params.limit)

    result = await db.execute(stmt)
    posts = result.scalars().all()

    return [
        await _build_post_response(db, post, user_id)
        for post in posts
    ]


async def _build_post_response(db, post: ForumPost, user_id) -> ForumPostRead:
    likes_count = await db.scalar(
        select(func.count()).where(PostLike.post_id == post.id)
    )

    comments_count = await db.scalar(
        select(func.count()).where(Comment.post_id == post.id)
    )

    is_liked = await db.scalar(
        select(func.count()).where(
            PostLike.post_id == post.id,
            PostLike.user_id == user_id
        )
    )

    return ForumPostRead(
        id=post.id,
        title=post.title,
        content=post.content,
        tags=post.tags.split(",") if post.tags else [],
        category=post.category,
        created_at=post.created_at,
        author=user_to_public_view(post.author),
        likes_count=likes_count or 0,
        comments_count=comments_count or 0,
        is_liked=bool(is_liked),
    )


## comments
async def create_comment(db, user_id, post_id, payload) -> CommentRead:
    comment = Comment(
        post_id=post_id,
        author_id=user_id,
        comment=payload.comment,
        created_at=datetime.utcnow()
    )
    db.add(comment)
    await db.commit()
    await db.refresh(comment)
    
    return CommentRead(
        id=comment.id,
        author=user_to_public_view(comment.author),
        comment=comment.comment,
        created_at=comment.created_at
    )


async def get_comments(db, post_id) -> list[CommentRead]:
    result = await db.execute(
        select(Comment)
        .where(Comment.post_id == post_id)
        .order_by(Comment.created_at)
    )
    comments = result.scalars().all()

    return [
        CommentRead(
            id=c.id,
            author=user_to_public_view(c.author),
            comment=c.comment,
            created_at=c.created_at
        )
        for c in comments
    ]


## like
async def toggle_like(db, user_id, post_id) -> LikeToggleResponse:
    result = await db.execute(
        select(PostLike).where(
            PostLike.post_id == post_id,
            PostLike.user_id == user_id
        )
    )
    existing = result.scalar_one_or_none()

    if existing:
        await db.delete(existing)
        is_liked = False
    else:
        db.add(PostLike(post_id=post_id, user_id=user_id))
        is_liked = True

    await db.commit()

    likes_count = await db.scalar(
        select(func.count()).where(PostLike.post_id == post_id)
    )

    return LikeToggleResponse(
        likes_count=likes_count or 0,
        is_liked=is_liked
    )


## study room
async def create_room(db: AsyncSession, user_id, payload: StudyRoomCreate) -> StudyRoomRead:
    room = StudyRoom(
        author_id=user_id,
        title=payload.title,
        description=payload.description,
        max_participants=payload.max_participants,
        created_at=datetime.utcnow()
    )
    db.add(room)
    await db.commit()
    await db.refresh(room)

    return await _build_room_response(db, room, user_id)

async def get_room_feed(db: AsyncSession, query: str, user_id: UUID) -> list[StudyRoomRead]:
    query = f"%{query}%"
    stmt = select(StudyRoom).where(
        or_(
            cast(StudyRoom.title, String).ilike(query),
            cast(StudyRoom.description, String).ilike(query),
        )
    )

    result = await db.execute(stmt)
    rooms = result.scalars().all()

    return await asyncio.gather(
        *[_build_room_response(db, room, user_id) for room in rooms]
    )

async def _build_room_response(db, room: StudyRoom, user_id) -> StudyRoomRead:
    likes_count = await db.scalar(
        select(func.count()).where(StudyRoomLike.room_id == room.id)
    )

    is_liked = await db.scalar(
        select(func.count()).where(
            StudyRoomLike.room_id == room.id,
            StudyRoomLike.user_id == user_id
        )
    )

    # TODO: doing this query twice for the join room function, possible optimization
    current_participant_count = await db.scalar(
        select(func.count()).where(StudyRoomParticipant.room_id == room.id)
    )

    return StudyRoomRead(
        id=room.id,
        title=room.title,
        description=room.description,
        created_at=room.created_at,
        author=user_to_public_view(room.author),
        likes_count=likes_count or 0,
        is_liked=bool(is_liked),
        current_participants=current_participant_count,
        max_participants=room.max_participants
    )

async def join_room(db, user_id, room_id) -> StudyRoomRead:
    room: StudyRoom = await db.get(StudyRoom, room_id)

    # TODO: handle potential race condition
    current_participant_count = await db.scalar(
        select(func.count()).where(StudyRoomParticipant.room_id == room_id)
    )
    if current_participant_count >= room.max_participants:
        raise HTTPException(
            status_code=403,
            detail="Room is full"
        )

    participant = StudyRoomParticipant(
        room_id=room_id,
        user_id=user_id
    )
    db.add(participant)
    await db.commit()

    return await _build_room_response(db, room, user_id)


async def leave_room(db, user_id, room_id):
    result = await db.execute(
        select(StudyRoomParticipant).where(
            StudyRoomParticipant.room_id == room_id,
            StudyRoomParticipant.user_id == user_id
        )
    )
    obj = result.scalar_one_or_none()

    if obj:
        await db.delete(obj)
        await db.commit()


## chat
async def get_messages(db, user_id, room_id, limit, before_id) -> list[ChatMessageRead]:
    await _check_study_room_membership(db, user_id, room_id)

    stmt = select(ChatMessage).where(ChatMessage.room_id == room_id)

    if before_id:
        stmt = stmt.where(ChatMessage.id < before_id)

    stmt = stmt.order_by(desc(ChatMessage.id)).limit(limit)

    result = await db.execute(stmt)
    messages = result.scalars().all()

    return [
        ChatMessageRead(
            id=m.id,
            room_id=m.room_id,
            author=user_to_public_view(m.author),
            content=m.content,
            created_at=m.created_at
        )
        for m in messages
    ]


async def send_message(db, user, room_id, payload) -> ChatMessageRead:
    await _check_study_room_membership(db, user.id, room_id)

    room: StudyRoom = await db.get(StudyRoom, room_id)
    if not room.is_active:
        raise HTTPException(
            status_code=403,
            detail="Study room is not active"
        )

    msg = ChatMessage(
        room_id=room_id,
        author_id=user.id,
        content=payload.content,
        created_at=datetime.utcnow()
    )
    db.add(msg)
    await db.commit()
    await db.refresh(msg)

    author = user_to_public_view(user)

    return ChatMessageRead(
        id=msg.id,
        room_id=msg.room_id,
        author=author,
        content=msg.content,
        created_at=msg.created_at
    )

async def _check_study_room_membership(db, user_id, room_id):
    result = await db.execute(
        select(StudyRoomParticipant).where(
            StudyRoomParticipant.room_id == room_id,
            StudyRoomParticipant.user_id == user_id
        ).limit(1)
    )
    obj = result.scalar_one_or_none()
    if not obj:
        raise HTTPException(
            status_code=403,
            detail="Study room member only endpoint"
        )