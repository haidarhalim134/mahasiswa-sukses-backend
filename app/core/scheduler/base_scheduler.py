from abc import ABC, abstractmethod
from typing import Any

class BaseScheduler(ABC):
    @abstractmethod
    def schedule_daily(self, task_url: str, secret: str) -> Any:
        pass

    @abstractmethod
    def schedule_weekly(self, task_url: str, secret: str) -> Any:
        pass

    @abstractmethod
    def schedule_delayed(self, task_url: str, secret: str, delay_seconds: int) -> Any:
        pass