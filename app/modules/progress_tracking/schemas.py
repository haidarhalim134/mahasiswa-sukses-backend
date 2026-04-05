from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel, Field
from enum import Enum
from typing import List, Optional
from datetime import datetime

# --- Enums ---

class TaskCategory(str, Enum):
    AKADEMIK = "Akademik"
    PRIBADI = "Pribadi"
    ORGANISASI = "Organisasi"

class TaskPriority(str, Enum):
    TINGGI = "Tinggi"
    SEDANG = "Sedang"
    RENDAH = "Rendah"

class TaskProgress(str, Enum):
    TODO = "Todo"
    ON_PROGRESS = "Proses"
    DONE = "Selesai"

# --- Schemas ---

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


