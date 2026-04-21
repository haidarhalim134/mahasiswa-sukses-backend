import requests
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from app.modules.task.schemas import TaskData
from app.core.scheduler.base_scheduler import BaseScheduler


scheduler = BackgroundScheduler()
scheduler.start()

class VPSScheduler(BaseScheduler):
    def schedule_daily(self, task_data: TaskData, secret: str):
        scheduler.add_job(
            lambda: requests.post(
                url=self.task_execute_url + f"?task_token={secret}",
                json=task_data.model_dump_json()
            ),
            trigger="cron",
            hour=0,
            minute=0,
            id=task_data.get_schedule_id(),
            replace_existing=True,
        )

    def schedule_weekly(self, task_data: TaskData, secret: str):
        scheduler.add_job(
            lambda: requests.post(
                url=self.task_execute_url + f"?task_token={secret}",
                json=task_data.model_dump_json()
            ),
            trigger="cron",
            day_of_week="sun",
            hour=0,
            minute=0,
            id=task_data.get_schedule_id(),
            replace_existing=True,
        )

    def schedule_delayed(self, task_data: TaskData, secret: str, delay_seconds: int):
        run_time = datetime.utcnow() + timedelta(seconds=delay_seconds)

        scheduler.add_job(
            lambda: requests.post(
                url=self.task_execute_url + f"?task_token={secret}",
                json=task_data.model_dump_json()
            ),
            trigger="date",
            run_date=run_time,
        )