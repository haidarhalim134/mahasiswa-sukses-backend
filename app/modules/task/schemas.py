import abc
from enum import Enum
from typing import Annotated, Literal, Union, override

from pydantic import BaseModel, Field

from app.modules.gamification.schemas import QuestFrequency


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