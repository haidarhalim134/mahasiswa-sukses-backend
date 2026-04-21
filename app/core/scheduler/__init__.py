import abc
from enum import Enum
import os
from typing import Annotated, Literal, Union, override

from pydantic import BaseModel, Field

from app.core.config import settings
from app.modules.gamification.schemas import QuestFrequency
from .base_scheduler import BaseScheduler

def get_scheduler() -> BaseScheduler:
    base_url = os.getenv("BASE_URL")
    if not base_url:
        base_url = os.getenv("VERCEL_PROJECT_PRODUCTION_URL")
        if base_url: 
            base_url = "https://" + base_url

    # task wont work anyway without base url
    assert base_url != None
    base_url+= "/api/v1/task/execute"

    if settings.app_env == "serverless":
        from .qstash_scheduler import QStashScheduler
        return QStashScheduler(base_url)

    from .vps_scheduler import VPSScheduler
    return VPSScheduler(base_url)

# TODO: maybe move these somewhere else
class TaskGroup(str, Enum):
    QUIZ = "quiz"
    NOTIFICATION = "notification"
    QUEST_RESET = "quest_reset"


class BaseTask(BaseModel, abc.ABC):
    task_group: TaskGroup

    @abc.abstractmethod
    def get_schedule_id(self):
        pass

# to ensure that quiz session is closed after the timer ran out
class QuizTask(BaseTask):
    task_group: Literal[TaskGroup.QUIZ] = TaskGroup.QUIZ
    quiz_id: int

    @override
    def get_schedule_id(self):
        return f"quiz_{self.quiz_id}"

# to send notification at certain time WIP
class NotificationTask(BaseTask):
    task_group: Literal[TaskGroup.NOTIFICATION] = TaskGroup.NOTIFICATION
    notification_id: int

    @override
    def get_schedule_id(self):
        return f"notification_{self.notification_id}"

class QuestResetTask(BaseTask):
    task_group: Literal[TaskGroup.QUEST_RESET] = TaskGroup.QUEST_RESET
    frequency: QuestFrequency

    @override
    def get_schedule_id(self):
        return f"quest_reset_{self.frequency}"


TaskData = Annotated[
    Union[QuizTask, NotificationTask, QuestResetTask],
    Field(discriminator="task_group"),
]