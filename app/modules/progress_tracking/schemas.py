from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel, Field, field_validator
from enum import Enum
from typing import List, Optional
from datetime import date, datetime, timedelta, timezone

class TaskCategory(str, Enum):
    AKADEMIK = "akademik"
    PRIBADI = "pribadi"
    ORGANISASI = "organisasi"

class TaskPriority(str, Enum):
    TINGGI = "tinggi"
    SEDANG = "sedang"
    RENDAH = "rendah"

class TaskProgress(str, Enum):
    TODO = "todo"
    ON_PROGRESS = "proses"
    DONE = "selesai"

class TaskBase(BaseModel):
    title: str
    category: TaskCategory
    priority: TaskPriority
    deadline: datetime
    description: Optional[str] = None

class TaskCreate(TaskBase):
    @field_validator('deadline')
    @classmethod
    def deadline_must_be_in_future(cls, v: datetime) -> datetime:
        # NOTE: hardcoded timezone, not the best solution
        ICT = timezone(timedelta(hours=7))
        if v.tzinfo is None:
            v = v.replace(tzinfo=ICT)
        else:
            v = v.astimezone(ICT)
        
        now_ict = datetime.now(ICT)
        if v.date() < now_ict.date():
            raise ValueError('The deadline cannot be in the past')
        return v

class TaskRead(TaskBase):
    id: int
    is_completed: bool = False

class TaskSummary(BaseModel):
    task_completed: int
    todo: int
    on_progress: int
    high_priority: int


