from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel, Field
from enum import Enum
from typing import List, Optional
from datetime import datetime

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
    pass

class TaskRead(TaskBase):
    id: int
    is_completed: bool = False

class TaskSummary(BaseModel):
    task_completed: int
    todo: int
    on_progress: int
    high_priority: int


