from datetime import datetime, timedelta
from sqlalchemy.engine.result import Result
from typing import Any, Optional
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import desc, func, select, update

from app.modules.gamification.gamification import ACHIEVEMENTS, QUESTS
from app.modules.gamification.models import AchievementHistory, QuestHistory, UserAchievement, UserQuest
from app.modules.gamification.schemas import (
    AchievementItem,
    AchievementType,
    HistoryItem,
    LeaderboardItem,
    QuestFrequency,
    QuestEvent,
    QuestItem,
)
from uuid import UUID

from app.users.models import User
from app.users.schemas import PublicUserView



def get_quest_def_by_event(event: QuestEvent):
    return [q for q in QUESTS if q["event"] == event]

def get_achievement_def_by_event(event: QuestEvent):
    return [q for q in ACHIEVEMENTS if q["event"] == event]

async def reset_quests_by_frequency(
    db: AsyncSession,
    frequency: QuestFrequency,
):
    # TODO: missing potential scheduler error which can reset quest more times than necessary
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

    quest_defs = get_quest_def_by_event(event)
    now = datetime.now(timezone.utc)

    for qdef in quest_defs:
        result = await db.execute(
            select(UserQuest).where(
                UserQuest.user_id == user.id,
                UserQuest.quest_id == qdef["id"],
            )
        )
        quest: UserQuest | None = result.scalar_one_or_none()

        if not quest:
            quest = UserQuest(
                user_id=user.id,
                quest_id=qdef["id"],
                progress=0,
                target=qdef["target"],
                frequency=qdef["frequency"],
            )
            db.add(quest)

        if quest.is_completed:
            continue

        cooldown = None
        if event ==  QuestEvent.STAY_10_MIN:
            cooldown = 9
        elif event == QuestEvent.STAY_1_HOUR:
            cooldown = 55

        if cooldown and quest.last_progress_at:
            delta = now - quest.last_progress_at

            minutes = int(delta.total_seconds() // 60)

            # soft anticheat, need to wait 9 min before progressing
            if minutes <= cooldown:
                continue

        if not cooldown or quest.last_progress_at:
            quest.progress += amount

        quest.last_progress_at = now

        if not quest.is_completed and quest.progress >= quest.target:
            quest.progress = quest.target
            quest.is_completed = True
            await add_xp(db, user, qdef["xp_reward"])
            
            history = QuestHistory(
                user_id=user.id,
                quest_id=qdef["id"],
                title=qdef["title"],
                xp_reward=qdef["xp_reward"],
                completed_at=datetime.now(timezone.utc)
            )

            db.add(history)

            # hook
            await progress_achievement(db, user, QuestEvent.COMPLETE_QUEST)

    await db.commit()


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

    for qdef in QUESTS:
        if frequency and qdef['frequency'] != frequency:
            continue

        progress = quest_map.get(qdef["id"])

        id = progress.id if progress else -1
        current_progress = progress.progress if progress else 0
        is_completed = progress.is_completed if progress else False

        progress_percentage = int((current_progress / qdef["target"]) * 100)

        item = QuestItem(**qdef, is_completed=is_completed, progress_percentage=progress_percentage)

        items.append(item)

    return items

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
            # title=adef["title"],
            # description=adef["description"],
            # xp_reward=adef["xp_reward"],
            # difficulty=adef["difficulty"], 
            # type=adef['type'],
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
    user.total_xp += amount

    await db.commit()

async def handle_daily_streak(db: AsyncSession, user: User):
    now = datetime.now(timezone.utc).date()

    if user.last_login_at and user.last_login_at.date() == now:
        return

    updated = await update_login_streak(user)

    if updated:
        await progress_quest(db, user, QuestEvent.USER_LOGIN)
        await progress_achievement(db, user, QuestEvent.USER_LOGIN)

        db.add(user)
        await db.commit()

async def update_login_streak(user: User):
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
    limit: int = 10
) -> list[LeaderboardItem]:
    result = await db.execute(
        select(User)
        .order_by(desc(User.total_xp))
        .limit(limit)
    )
    users = result.scalars().all()

    leaderboard: list[LeaderboardItem] = []
    for idx, user in enumerate(users, start=1):
        leaderboard.append(LeaderboardItem(
            rank=idx,
            user=PublicUserView(
                id=user.id,
                full_name=user.full_name
            ),
            xp=user.total_xp
        ))

    return leaderboard

async def get_user_rank(db: AsyncSession, user_id: UUID) -> int:
    result = await db.execute(
        select(User.total_xp).where(User.id == user_id)
    )
    user_xp = result.scalar_one_or_none()

    if user_xp is None:
        raise ValueError("User not found")

    result = await db.execute(
        select(func.count())
        .select_from(User)
        .where(
            User.total_xp > user_xp
        )
    )

    higher_count = result.scalar_one()

    return higher_count + 1

async def get_user_history(
    db: AsyncSession,
    user_id: UUID
) -> list[HistoryItem]:

    # Fetch latest 50 quest history
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

    # Fetch latest 50 achievement history
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

    # Final sort (merge both sources)
    history.sort(key=lambda x: x.completed_at, reverse=True)

    # Hard limit to 50 total items
    return history[:50]