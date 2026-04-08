import os

from app.core.config import settings
from .base_scheduler import BaseScheduler

def get_scheduler() -> BaseScheduler:
    if settings.app_env == "serverless":
        from .qstash_scheduler import QStashScheduler
        return QStashScheduler()

    from .vps_scheduler import VPSScheduler
    return VPSScheduler()