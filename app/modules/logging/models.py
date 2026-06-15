import datetime
from typing import Any, Optional
from uuid import UUID
from sqlmodel import Field, JSON, Column

from app.db.base import Base

class ErrorLog(Base, table=True):
    __tablename__ = "error_logs"

    id: Optional[int] = Field(default=None, primary_key=True)
    timestamp: datetime.datetime = Field(default_factory=datetime.datetime.utcnow, index=True)
    
    exception_type: str = Field(index=True)
    message: str
    traceback: str
    
    path: str
    method: str
    
    user_id: Optional[UUID] = Field(default=None, index=True)
    user_role: Optional[str] = Field(default=None)
    
    request_data: Optional[dict] = Field(default=None, sa_column=Column(JSON))