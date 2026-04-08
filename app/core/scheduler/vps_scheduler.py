import requests
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from app.core.scheduler.base_scheduler import BaseScheduler


scheduler = BackgroundScheduler()
scheduler.start()

class VPSScheduler(BaseScheduler):
    def schedule_daily(self, task_url: str, secret: str):
        scheduler.add_job(
            lambda: requests.post(task_url + f"?task_token={secret}"),
            trigger="cron",
            hour=0,
            minute=0,
            id="daily_task",
            replace_existing=True,
        )

    def schedule_weekly(self, task_url: str, secret: str):
        scheduler.add_job(
            lambda: requests.post(task_url + f"?task_token={secret}"),
            trigger="cron",
            day_of_week="sun",
            hour=0,
            minute=0,
            id="weekly_task",
            replace_existing=True,
        )

    def schedule_delayed(self, task_url: str, secret: str, delay_seconds: int):
        run_time = datetime.utcnow() + timedelta(seconds=delay_seconds)

        scheduler.add_job(
            lambda: requests.post(task_url + f"?task_token={secret}"),
            trigger="date",
            run_date=run_time,
        )