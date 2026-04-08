from qstash import QStash
import os

from app.core.config import settings
from app.core.scheduler.base_scheduler import BaseScheduler

qstash = QStash(settings.qstash_token)

class QStashScheduler(BaseScheduler):
    def schedule_daily(self, task_url: str, secret: str):
        qstash.schedule.create(
            destination=task_url + f"?task_token={secret}",
            cron="0 0 * * *",
            schedule_id="daily-task",
        )

    def schedule_weekly(self, task_url: str, secret: str):
        qstash.schedule.create(
            destination=task_url + f"?task_token={secret}",
            cron="0 0 * * 0",
            schedule_id="weekly-task",
        )

    def schedule_delayed(self, task_url: str, secret: str, delay_seconds: int):
        qstash.message.publish_json(
            url=task_url + f"?task_token={secret}",
            body={},
            delay=delay_seconds,
        )