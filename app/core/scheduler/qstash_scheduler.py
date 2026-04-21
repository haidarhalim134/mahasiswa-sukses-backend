from qstash import QStash
import os

from app.core.config import settings
from app.modules.task.schemas import TaskData
from app.core.scheduler.base_scheduler import BaseScheduler

qstash = QStash(settings.qstash_token)

class QStashScheduler(BaseScheduler):
    def schedule_daily(self, task_data: TaskData, secret: str):
        qstash.schedule.create(
            destination=self.task_execute_url + f"?task_token={secret}",
            cron="0 0 * * *",
            body=task_data.model_dump_json(), 
            schedule_id=task_data.get_schedule_id(),
        )

    def schedule_weekly(self, task_data: TaskData, secret: str):
        qstash.schedule.create(
            destination=self.task_execute_url + f"?task_token={secret}",
            cron="0 0 * * 0",
            body=task_data.model_dump_json(), 
            schedule_id=task_data.get_schedule_id(),
        )

    def schedule_delayed(self, task_data: TaskData, secret: str, delay_seconds: int):
        qstash.message.publish_json(
            url=self.task_execute_url + f"?task_token={secret}",
            body=task_data.model_dump_json(), 
            delay=delay_seconds,
        )