import asyncio
from datetime import datetime, timezone
from uuid import UUID
from fastapi import HTTPException
from sqlmodel import String, cast, or_, select, func, desc, update
from sqlalchemy.orm import aliased
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.community.models import (
    ForumPost, Comment, PostLike, RoomChatLike,
    StudyRoom, StudyRoomLike, StudyRoomParticipant, ChatMessage
)
from app.modules.community.schemas import (
    ChatMessageCreate,
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
from app.modules.gamification.schemas import QuestEvent
from app.modules.gamification.services import progress_quest
from app.users.schemas import PublicUserView
from app.users.service import get_online_users_count, get_user_by_id, user_to_public_view


## stats
async def get_stats(db: AsyncSession) -> CommunityStats:
    active_rooms_count = await db.scalar(
        select(func.count()).where(
            StudyRoom.is_active == True
        )
    )

    return CommunityStats(
        online_count=await get_online_users_count(db),
        active_rooms_count=active_rooms_count or 0
    )


## posts
async def create_post(db: AsyncSession, user_id, payload: ForumPostCreate) -> ForumPostRead:
    post = ForumPost(
        author_id=user_id,
        title=payload.title,
        content=payload.content,
        tags=",".join(payload.tags),
        category=payload.category,
        created_at=datetime.now(timezone.utc)
    )
    db.add(post)
    await db.commit()
    await db.refresh(post)

    return _build_post_response(post, 0, 0, False)


async def get_post(db: AsyncSession, post_id: int, user_id: UUID) -> ForumPostRead | None:
    result = await db.execute(
        get_post_with_stats_stmt(user_id)
        .where(ForumPost.id == post_id)
        .order_by(desc(ForumPost.created_at))
    )
    row = result.first()

    if not row:
        return None

    return _build_post_response(*row)


async def get_forum_feed(db: AsyncSession, params: ForumFeedParams, user_id: UUID) -> list[ForumPostRead]:
    stmt = get_post_with_stats_stmt(user_id).order_by(desc(ForumPost.created_at))

    if params.tag:
        stmt = stmt.where(cast(ForumPost.tags, String).contains(params.tag))
    
    if params.category:
        stmt = stmt.where(ForumPost.category == params.category)

    stmt = stmt.offset(params.offset).limit(params.limit)

    result = await db.execute(stmt)
    rows = result.all()

    return [
        _build_post_response(*row)
        for row in rows
    ]

# no longer syncronous
def get_post_with_stats_stmt(user_id: UUID):
    likes_subq = select(func.count()).where(
        PostLike.post_id == ForumPost.id, PostLike.like == True
    ).correlate(ForumPost).scalar_subquery()

    comments_subq = select(func.count()).where(
        Comment.post_id == ForumPost.id
    ).correlate(ForumPost).scalar_subquery()

    is_liked_subq = select(func.count() > 0).where(
        PostLike.post_id == ForumPost.id, PostLike.user_id == user_id, PostLike.like == True
    ).correlate(ForumPost).scalar_subquery()

    return select(
        ForumPost,
        likes_subq.label("likes_count"),
        comments_subq.label("comments_count"),
        is_liked_subq.label("is_liked")
    )

def _build_post_response(post: ForumPost, likes_count, comments_count, is_liked):
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
        created_at=datetime.now(timezone.utc)
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
async def toggle_post_like(db: AsyncSession, user, post_id) -> LikeToggleResponse:
    user_id = user.id

    result = await db.execute(
        select(PostLike).where(
            PostLike.post_id == post_id,
            PostLike.user_id == user_id
        )
    )
    existing = result.scalar_one_or_none()

    if existing:
        is_liked = not existing.like
        
        await db.execute(
            update(PostLike)
            .where(
                PostLike.post_id == post_id,
                PostLike.user_id == user_id
            )
            .values(
                like=not existing.like
            )
        )
    else:
        db.add(PostLike(post_id=post_id, user_id=user_id))
        is_liked = True

        # handle quest progress
        post_result = await db.execute(
            select(ForumPost).where(ForumPost.id == post_id)
        )
        post = post_result.scalar_one_or_none()
        if post and post.author_id != user_id:
            await progress_quest(db, post.author, QuestEvent.RECEIVE_LIKE)

    await db.commit()

    likes_count = await db.scalar(
        select(func.count()).where(PostLike.post_id == post_id, PostLike.like == True)
    )

    return LikeToggleResponse(
        likes_count=likes_count or 0,
        is_liked=is_liked
    )

async def toggle_room_like(db, user_id, room_id) -> LikeToggleResponse:
    result = await db.execute(
        select(StudyRoomLike).where(
            StudyRoomLike.room_id == room_id,
            StudyRoomLike.user_id == user_id
        )
    )
    existing = result.scalar_one_or_none()

    if existing:
        await db.delete(existing)
        is_liked = False
    else:
        db.add(StudyRoomLike(room_id=room_id, user_id=user_id))
        is_liked = True

    await db.commit()

    likes_count = await db.scalar(
        select(func.count()).where(StudyRoomLike.room_id == room_id)
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
        created_at=datetime.now(timezone.utc)
    )
    db.add(room)
    await db.commit()
    await db.refresh(room)

    return await _build_room_response(db, room, user_id)

async def get_room_feed(db: AsyncSession, query: str, user_id: UUID) -> list[StudyRoomRead]:
    stmt = select(StudyRoom).order_by(desc(StudyRoom.created_at))

    if query:
        query = f"%{query}%"
        stmt = stmt.where(
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

    is_joined = await db.scalar(
        select(func.count()).where(
            StudyRoomParticipant.room_id == room.id,
            StudyRoomParticipant.user_id == user_id
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
        is_joined=is_joined,
        is_active=room.is_active,
        author=user_to_public_view(room.author),
        likes_count=likes_count or 0,
        is_liked=bool(is_liked),
        current_participants=current_participant_count,
        max_participants=room.max_participants
    )

async def join_room(db: AsyncSession, user_id, room_id) -> StudyRoomRead:
    room = await db.get(StudyRoom, room_id)
    if not room:
        raise HTTPException(
            status_code=404,
            detail="Study room not found"
        )

    # TODO: handle potential race condition
    current_participant_count = await db.scalar(
        select(func.count()).where(StudyRoomParticipant.room_id == room_id)
    )
    if current_participant_count and current_participant_count >= room.max_participants:
        raise HTTPException(
            status_code=403,
            detail="Room is full"
        )
    result = await db.execute(
        select(StudyRoomParticipant).where(
            StudyRoomParticipant.room_id == room_id,
            StudyRoomParticipant.user_id == user_id
        ).limit(1)
    )
    obj = result.scalar_one_or_none()
    if not obj:
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

    ReplyAlias = aliased(ChatMessage)

    stmt = (
        select(
            ChatMessage, 
            func.count(RoomChatLike.chat_id).label("likes_count"),
            func.count(ReplyAlias.id).label("reply_count"),
            func.bool_or(RoomChatLike.user_id == user_id).label("is_liked")
        )
        .outerjoin(RoomChatLike, ChatMessage.id == RoomChatLike.chat_id)
        .outerjoin(ReplyAlias, ChatMessage.id == ReplyAlias.replying_to)
        .where(ChatMessage.room_id == room_id)
        .group_by(ChatMessage.id)
    )

    if before_id:
        stmt = stmt.where(ChatMessage.id < before_id)

    stmt = stmt.order_by(desc(ChatMessage.id)).limit(limit)

    result = await db.execute(stmt)
    rows = result.all()

    return [
        ChatMessageRead(
            id=m.id,
            room_id=m.room_id,
            author=user_to_public_view(m.author),
            content=m.content,
            is_liked=is_liked or False,
            likes_count=l_count, 
            reply_count=r_count,
            replying_to=m.replying_to,
            created_at=m.created_at
        )
        for m, l_count, r_count, is_liked in rows
    ]


async def send_message(db, user, room_id, payload: ChatMessageCreate) -> ChatMessageRead:
    await _check_study_room_membership(db, user.id, room_id)

    room: StudyRoom = await db.get(StudyRoom, room_id)
    if not room.is_active:
        raise HTTPException(
            status_code=403,
            detail="Study room is not active"
        )

    if payload.replying_to:
        earlier_chat: ChatMessage = await db.get(ChatMessage, payload.replying_to)
        if not earlier_chat or earlier_chat.room_id != room_id:
            raise HTTPException(
                status_code=403,
                detail="Replying to non existing chat or chat from other room."
            )

    msg = ChatMessage(
        room_id=room_id,
        author_id=user.id,
        content=payload.content,
        created_at=datetime.now(timezone.utc)
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
        is_liked=False,
        likes_count=0, # because its new
        reply_count=0,
        replying_to=msg.replying_to,
        created_at=msg.created_at
    )

async def toggle_room_chat_like(db, user_id, room_chat_id) -> LikeToggleResponse:
    chat: ChatMessage = await db.get(ChatMessage, room_chat_id)
    await _check_study_room_membership(db, user_id, chat.room_id)

    result = await db.execute(
        select(RoomChatLike).where(
            RoomChatLike.chat_id == room_chat_id,
            RoomChatLike.user_id == user_id
        )
    )
    existing = result.scalar_one_or_none()

    if existing:
        await db.delete(existing)
        is_liked = False
    else:
        db.add(RoomChatLike(chat_id=room_chat_id, user_id=user_id, room_id=chat.room_id))
        is_liked = True

    await db.commit()

    likes_count = await db.scalar(
        select(func.count()).where(RoomChatLike.chat_id == room_chat_id)
    )

    return LikeToggleResponse(
        likes_count=likes_count or 0,
        is_liked=is_liked
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