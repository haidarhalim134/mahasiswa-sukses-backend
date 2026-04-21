from abc import ABC, abstractmethod
from typing import Any

from app.core.scheduler import TaskData

class BaseScheduler(ABC):
    task_execute_url: str
    
    def __init__(self, task_execute_url: str) -> None:
        super().__init__()
        self.task_execute_url = task_execute_url
        
    @abstractmethod
    def schedule_daily(self, task_data: TaskData, secret: str) -> Any:
        pass

    @abstractmethod
    def schedule_weekly(self, task_data: TaskData, secret: str) -> Any:
        pass

    @abstractmethod
    def schedule_delayed(self, task_data: TaskData, secret: str, delay_seconds: int) -> Any:
        pass