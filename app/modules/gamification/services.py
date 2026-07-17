from datetime import datetime, timedelta
from fastapi import HTTPException, status
from sqlalchemy import Case
from sqlalchemy.engine.result import Result
from typing import Any, Optional
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import and_, desc, func, or_, select, update

from app.modules.friends.models import Friendship
from app.modules.friends.schemas import FriendshipStatus
from app.modules.gamification.gamification import ACHIEVEMENTS
from app.modules.gamification.models import AchievementHistory, Quest, QuestHistory, UserAchievement, UserQuest
from app.modules.gamification.schemas import (
    AchievementItem,
    AchievementType,
    HistoryItem,
    LeaderboardItem,
    QuestCreate,
    QuestDef,
    QuestFrequency,
    QuestEvent,
    QuestItem,
    QuestUpdate,
)
from uuid import UUID

from app.users.models import User
from app.users.schemas import PublicUserView
from app.users.service import get_user_by_id, log_login_history, user_to_public_view, add_xp as add_user_xp



async def get_quests_by_event(db: AsyncSession, event: QuestEvent):
    statement = select(Quest).where(Quest.event == event.value)
    result = await db.execute(statement)
    return result.scalars().all()

async def get_quests_by_frequency(db: AsyncSession, frequency: Optional[QuestFrequency]):
    statement = select(Quest)
    if frequency:
        statement = statement.where(Quest.frequency == frequency.value)
    result = await db.execute(statement)
    return result.scalars().all()

def get_achievement_def_by_event(event: QuestEvent):
    return [q for q in ACHIEVEMENTS if q["event"] == event]

async def reset_quests_by_frequency(
    db: AsyncSession,
    frequency: QuestFrequency,
):
    # NOTE: missing potential scheduler error which can reset quest more times than necessary
    _ = await db.execute(
        update(UserQuest)
        .where(
            UserQuest.frequency == frequency, # pyright: ignore[reportArgumentType]
        )
        .values(
            progress=0,
            is_completed=False,
            last_progress_at=None
        )
    )

    await db.commit()

## quest
async def progress_quest(
    db: AsyncSession,
    user: User,
    event: QuestEvent,
    amount: int = 1,
):
    """
    Progress quests based on event, for quest with cooldown first call will start the cooldown and the next call after cooldown will progress the quest
    """
    quest_defs = await get_quests_by_event(db, event)
    now = datetime.now(timezone.utc)

    for qdef in quest_defs:
        if not qdef.is_active:
            continue
        quest = await _get_or_create_user_quest(db, user.id, qdef)
        
        if quest.is_completed:
            continue

        # Extracted logic handles individual quest updates
        await _update_quest_progress(db, user, quest, qdef, event, amount, now)

    await db.commit()

# progress_quest helpers
async def _update_quest_progress(
    db: AsyncSession,
    user: User,
    quest: UserQuest,
    qdef: Quest,
    event: QuestEvent,
    amount: int,
    now: datetime,
) -> None:
    if event == QuestEvent.STAY_1_HOUR and quest.last_progress_at:
        if not await _check_is_continuous(db, user.id, now):
            quest.last_progress_at = now
            return

    if _is_on_cooldown(quest, event, now):
        return
    
    if not _get_cooldown_minutes(event) or quest.last_progress_at:
        quest.progress += amount

    quest.last_progress_at = now

    if quest.progress >= quest.target:
        await _handle_quest_completion(db, user, quest, qdef)

async def _get_or_create_user_quest(db: AsyncSession, user_id: UUID, qdef: Quest) -> UserQuest:
    result = await db.execute(
        select(UserQuest).where(
            UserQuest.user_id == user_id,
            UserQuest.quest_id == qdef.id,
        )
    )
    quest = result.scalar_one_or_none()
    if not quest:
        quest = UserQuest(
            user_id=user_id,
            quest_id=qdef.id,
            progress=0,
            target=qdef.target,
            frequency=qdef.frequency,
        )
        db.add(quest)
    return quest


def _get_cooldown_minutes(event: QuestEvent) -> int | None:
    if event == QuestEvent.STAY_10_MIN:
        return 9
    if event == QuestEvent.STAY_1_HOUR:
        return 55
    return None


def _is_on_cooldown(quest: UserQuest, event: QuestEvent, now: datetime) -> bool:
    cooldown = _get_cooldown_minutes(event)
    if cooldown and quest.last_progress_at:
        delta = now - quest.last_progress_at
        minutes = int(delta.total_seconds() // 60)
        return minutes <= cooldown
    return False


async def _check_is_continuous(db: AsyncSession, user_id: int, now: datetime) -> bool:
    ten_min_qdef = get_quest_def_by_event(QuestEvent.STAY_10_MIN)[0]
    res_10 = await db.execute(
        select(UserQuest).where(
            UserQuest.user_id == user_id,
            UserQuest.quest_id == ten_min_qdef.id
        )
    )
    quest_10 = res_10.scalar_one_or_none()
    
    if not quest_10 or not quest_10.last_progress_at:
        return False
        
    heartbeat_delta = now - quest_10.last_progress_at
    return (heartbeat_delta.total_seconds() / 60) <= 13


async def _handle_quest_completion(db: AsyncSession, user: User, quest: UserQuest, qdef: Quest):
    quest.progress = quest.target
    quest.is_completed = True
    await add_xp(db, user, qdef.xp_reward)
    
    history = QuestHistory(
        user_id=user.id,
        quest_id=qdef.id,
        title=qdef.title,
        xp_reward=qdef.xp_reward,
        completed_at=datetime.now(timezone.utc)
    )
    db.add(history)
    await progress_achievement(db, user, QuestEvent.COMPLETE_QUEST)
# progress_quest helpers

async def get_user_quests(
    db: AsyncSession,
    user_id: UUID,
    frequency: QuestFrequency | None
) -> list[QuestItem]:
    """
    Return all quests with progress (merge DB + QuestDef)
    """
    stmt = select(UserQuest).where(UserQuest.user_id == user_id)
    if frequency:
        stmt = stmt.where(UserQuest.frequency == frequency)

    # get user progress
    result = await db.execute(stmt)
    user_quests = result.scalars().all()

    quest_map = {q.quest_id: q for q in user_quests}

    items = []

    for qdef in await get_quests_by_frequency(db, frequency):
        if not qdef.is_active:
            continue
        progress = quest_map.get(qdef.id)

        current_progress = progress.progress if progress else 0
        is_completed = progress.is_completed if progress else False

        progress_percentage = int((current_progress / qdef.target) * 100)

        item = QuestItem(title=qdef.title, description=qdef.description, frequency=qdef.frequency, xp_reward=qdef.xp_reward, difficulty=qdef.difficulty, is_completed=is_completed, progress_percentage=progress_percentage)

        items.append(item)

    return items

async def get_user_quest_stats(db: AsyncSession, user_id: UUID) -> tuple[int, int]:
    stmt = (
        select(
            func.count(UserQuest.id).label("total"),
            func.sum(Case((UserQuest.is_completed == True, 1), else_=0)).label("completed")
        )
        .where(
            UserQuest.user_id == user_id,
            UserQuest.frequency.in_([QuestFrequency.DAILY, QuestFrequency.WEEKLY])
        )
    )
    
    result = await db.execute(stmt)
    row = result.fetchone()
    
    total_tracked = row.total if row and row.total else 0
    total_completed = row.completed if row and row.completed else 0
    
    return total_tracked, total_completed

## achievement
async def progress_achievement(
    db: AsyncSession,
    user: User,
    event: QuestEvent,
    amount: int = 1,
):
    achievement_defs = get_achievement_def_by_event(event)

    for adef in achievement_defs:
        result = await db.execute(
            select(UserAchievement).where(
                UserAchievement.user_id == user.id,
                UserAchievement.achievement_id == adef["id"],
            )
        )
        achievement = result.scalar_one_or_none()

        if not achievement:
            achievement = UserAchievement(
                user_id=user.id,
                achievement_id=adef["id"],
                progress=0,
                type=adef['type'],
                target=adef["target"],
            )
            db.add(achievement)

        if achievement.is_completed:
            continue
        
        # if streak, set instead to the current streak, once it reaches the required streak, it should not be updated anymore
        if event == QuestEvent.USER_LOGIN_STREAK:
            achievement.progress = amount
        else:
            achievement.progress += amount

        if not achievement.is_completed and achievement.progress >= achievement.target:
            achievement.progress = achievement.target
            achievement.is_completed = True
            achievement.completion_date = datetime.now(timezone.utc).date()

            await add_xp(db, user, adef["xp_reward"])

            history = AchievementHistory(
                user_id=user.id,
                achievement_id=adef["id"],
                title=adef["title"],
                xp_reward=adef["xp_reward"],
                completed_at=datetime.now(timezone.utc)
            )

            db.add(history)

    await db.commit()

async def get_user_achievements(
    db: AsyncSession,
    user_id: UUID,
    achievemnt_type: AchievementType | None=None
) -> list[AchievementItem]:  # you can reuse or create AchievementItem later
    """
    Return all achievements with progress
    """
    stmt = select(UserAchievement).where(UserAchievement.user_id == user_id)
    if achievemnt_type:
        stmt = stmt.where(UserAchievement.type == achievemnt_type)

    result = await db.execute(stmt)
    user_achievements = result.scalars().all()

    achievement_map = {a.achievement_id: a for a in user_achievements}

    items = []

    for adef in ACHIEVEMENTS:
        if achievemnt_type and adef['type'] != achievemnt_type:
            continue
        
        progress = achievement_map.get(adef["id"])

        current_progress = progress.progress if progress else 0
        is_completed = progress.is_completed if progress else False
        completion_date = progress.completion_date if progress else None

        progress_percentage = int((current_progress / adef["target"]) * 100)

        item = AchievementItem(
            **adef,
            progress_percentage=progress_percentage,
            is_completed=is_completed,
            completion_date=completion_date
        )

        items.append(item)

    return items

async def add_xp(
    db: AsyncSession,
    user: User,
    amount: int,
):
    await add_user_xp(db, user, amount)

    await db.commit()

async def handle_daily_streak(db: AsyncSession, user: User):
    now = datetime.now(timezone.utc).date()

    if user.last_login_at and user.last_login_at.date() == now:
        return

    updated = update_login_streak(user)

    if updated:
        await log_login_history(db, user.id)
        await progress_quest(db, user, QuestEvent.USER_LOGIN)
        await progress_achievement(db, user, QuestEvent.USER_LOGIN)

        await progress_achievement(db, user, QuestEvent.USER_LOGIN_STREAK, user.current_streak)

        db.add(user)
        await db.commit()

def update_login_streak(user: User):
    now = datetime.now(timezone.utc).date()

    if user.last_login_at:
        last_login_date = user.last_login_at.date()
        diff = (now - last_login_date).days

        if diff == 0:
            return False

        elif diff == 1:
            user.current_streak += 1

        else:
            user.current_streak = 1
    else:
        user.current_streak = 1

    if user.current_streak > user.longest_streak:
        user.longest_streak = user.current_streak

    user.last_login_at = datetime.now(timezone.utc)

    return True 

async def generate_leaderboard(
    db: AsyncSession,
    user: User,
    limit: int = 10
) -> list[LeaderboardItem]:
    result = await db.execute(
        select(User)
        .where(or_(User.share_leaderboard_stats == True, User.id == user.id), User.total_xp > 0)
        .order_by(desc(User.total_xp), User.full_name.asc())
        .limit(limit)
    )
    users = result.scalars().all()

    leaderboard: list[LeaderboardItem] = []
    for idx, u in enumerate(users, start=1):
        leaderboard.append(LeaderboardItem(
            rank=idx,
            user=user_to_public_view(u),
            xp=u.total_xp,
            level=u.level
        ))

    return leaderboard

async def generate_friends_leaderboard(
    db: AsyncSession,
    user: User,
    limit: int = 10
) -> list[LeaderboardItem]:
    friends_ids_query = select(Friendship.requester_id).where(
        and_(Friendship.requested_id == user.id, Friendship.status == FriendshipStatus.ACCEPTED)
    ).union(
        select(Friendship.requested_id).where(
            and_(Friendship.requester_id == user.id, Friendship.status == FriendshipStatus.ACCEPTED)
        )
    )

    stmt = (
        select(User)
        .where(
            or_(
                User.id == user.id,
                User.id.in_(friends_ids_query)
            )
        )
        .order_by(desc(User.total_xp), User.full_name.asc())
        .limit(limit)
    )

    result = await db.execute(stmt)
    users = result.scalars().all()

    leaderboard: list[LeaderboardItem] = []
    for idx, u in enumerate(users, start=1):
        leaderboard.append(LeaderboardItem(
            rank=idx,
            user=user_to_public_view(u),
            xp=u.total_xp,
            level=u.level
        ))

    return leaderboard

async def get_user_rank(db: AsyncSession, user: User) -> int:

    result = await db.execute(
        select(func.count())
        .select_from(User)
        .where(
            or_(User.share_leaderboard_stats == True, User.id == user.id),
            or_(
                User.total_xp > user.total_xp,
                # same xp, ordered first due to name
                and_(
                    User.total_xp == user.total_xp,
                    User.full_name < user.full_name
                ),
            )
        )
    )

    higher_count = result.scalar_one()

    return higher_count + 1

async def get_user_history(
    db: AsyncSession,
    user_id: UUID
) -> list[HistoryItem]:

    quest_result = await db.execute(
        select(
            QuestHistory.id,
            QuestHistory.title,
            QuestHistory.xp_reward,
            QuestHistory.completed_at,
        )
        .where(QuestHistory.user_id == user_id)
        .order_by(QuestHistory.completed_at.desc())
        .limit(50)
    )

    achievement_result = await db.execute(
        select(
            AchievementHistory.id,
            AchievementHistory.title,
            AchievementHistory.xp_reward,
            AchievementHistory.completed_at,
        )
        .where(AchievementHistory.user_id == user_id)
        .order_by(AchievementHistory.completed_at.desc())
        .limit(50)
    )

    history = []

    for q in quest_result.all():
        history.append(HistoryItem(
            id=q.id,
            title=q.title,
            xp_reward=q.xp_reward,
            type="quest",
            completed_at=q.completed_at
        ))

    for a in achievement_result.all():
        history.append(HistoryItem(
            id=a.id,
            title=a.title,
            xp_reward=a.xp_reward,
            type="achievement",
            completed_at=a.completed_at
        ))

    history.sort(key=lambda x: x.completed_at, reverse=True)

    return history[:50]


async def list_quests_service(db: AsyncSession, skip: int = 0, limit: int = 100):
    query = select(Quest).offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


async def get_quest_service(quest_id: str, db: AsyncSession):
    quest = await db.get(Quest, quest_id)
    if not quest:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Quest not found"
        )
    return quest


async def create_quest_service(payload: QuestCreate, db: AsyncSession):
    new_quest = Quest(**payload.model_dump())
    db.add(new_quest)
    await db.commit()
    await db.refresh(new_quest)
    return new_quest


async def set_active_service(quest_id: str, active: bool, db: AsyncSession):
    quest = await get_quest_service(quest_id, db)  # Reusable check
    
    quest.is_active = active
    db.add(quest)
    await db.commit()
    return


async def update_quest_service(quest_id: str, payload: QuestUpdate, db: AsyncSession):
    quest = await get_quest_service(quest_id, db)  # Reusable check
    
    update_data = payload.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(quest, key, value)
        
    db.add(quest)
    await db.commit()
    await db.refresh(quest)
    return quest


async def delete_quest_service(quest_id: str, db: AsyncSession):
    quest = await get_quest_service(quest_id, db)  # Reusable check
    
    await db.delete(quest)
    await db.commit()
    return