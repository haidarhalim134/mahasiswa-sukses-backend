from datetime import datetime
from uuid import UUID
from fastapi import HTTPException
from sqlmodel import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.community.models import (
    ForumPost, Comment, PostLike,
    StudyRoom, StudyRoomParticipant, ChatMessage
)
from app.modules.community.schemas import (
    CommunityStats,
    ForumFeedParams,
    ForumPostRead,
    CommentRead,
    LikeToggleResponse,
    ChatMessageRead,
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
async def create_post(db: AsyncSession, user_id, payload) -> ForumPostRead:
    post = ForumPost(
        author_id=user_id,
        title=payload.title,
        content=payload.content,
        tags=",".join(payload.tags),
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
        stmt = stmt.where(ForumPost.tags.contains(params.tag))

    stmt = stmt.offset(params.offset).limit(params.limit)

    result = await db.execute(stmt)
    posts = result.scalars().all()

    return [
        await _build_post_response(db, post, user_id)
        for post in posts
    ]


async def _build_post_response(db, post, user_id) -> ForumPostRead:
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
        created_at=post.created_at,
        author=user_to_public_view(post.author),
        likes_count=likes_count or 0,
        comments_count=comments_count or 0,
        is_liked=bool(is_liked)
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

    author = user_to_public_view(room.author)

    return StudyRoomRead(
        **room.model_dump(),
        author=author,
        is_joined=True,
        current_participants=current_participant_count + 1
    )


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
    _check_study_room_membership(db, user_id, room_id)

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
    _check_study_room_membership(db, user.id, room_id)

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