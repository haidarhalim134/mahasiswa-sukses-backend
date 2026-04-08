from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select, update

from app.modules.gamification.quest import QUESTS
from app.modules.gamification.models import UserQuest
from app.modules.gamification.schemas import (
    QuestFrequency,
    QuestEvent,
    QuestItem,
)
import uuid



def get_quest_def_by_event(event: QuestEvent):
    return [q for q in QUESTS if q["event"] == event]


async def reset_quests_by_frequency(
    db: AsyncSession,
    user_id: uuid.UUID,
    frequency: QuestFrequency,
):
    _ = await db.execute(
        update(UserQuest)
        .where(
            UserQuest.user_id == user_id,  # pyright: ignore[reportArgumentType]
            UserQuest.frequency == frequency, # pyright: ignore[reportArgumentType]
        )
        .values(
            progress=0,
            is_completed=False,
        )
    )

    await db.commit()


async def progress_quest(
    db: AsyncSession,
    user_id: uuid.UUID,
    event: QuestEvent,
    amount: int = 1,
):
    """
    Progress quests based on event
    """

    quest_defs = get_quest_def_by_event(event)

    for qdef in quest_defs:
        result = await db.execute(
            select(UserQuest).where(
                UserQuest.user_id == user_id,
                UserQuest.quest_id == qdef["id"],
            )
        )
        quest: Optional[UserQuest] = result.scalar_one_or_none()

        if not quest:
            quest = UserQuest(
                user_id=user_id,
                quest_id=qdef["id"],
                progress=0,
                target=qdef["target"],
                frequency=qdef["frequency"],
            )
            db.add(quest)

        if quest.is_completed:
            continue

        quest.progress += amount

        if quest.progress >= quest.target:
            quest.progress = quest.target
            quest.is_completed = True

    await db.commit()


async def get_user_quests(
    db: AsyncSession,
    user_id: uuid.UUID,
    frequency: QuestFrequency
) -> list[QuestItem]:
    """
    Return all quests with progress (merge DB + QuestDef)
    """

    # get user progress
    result = await db.execute(
        select(UserQuest).where(UserQuest.user_id == user_id, UserQuest.frequency == frequency)
    )
    user_quests = result.scalars().all()

    quest_map = {q.quest_id: q for q in user_quests}

    items = []

    for qdef in QUESTS:
        if qdef['frequency'] != frequency:
            continue

        progress = quest_map.get(qdef["id"])

        id = progress.id if progress else -1
        current_progress = progress.progress if progress else 0
        is_completed = progress.is_completed if progress else False

        progress_percentage = int((current_progress / qdef["target"]) * 100)

        item = QuestItem(**qdef, is_completed=is_completed, progress_percentage=progress_percentage)

        items.append(item)

    return items