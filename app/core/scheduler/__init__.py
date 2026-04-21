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