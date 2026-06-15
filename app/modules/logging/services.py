import traceback
from typing import Optional
from uuid import UUID
from fastapi import Request, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from sqlmodel.ext.asyncio.session import AsyncSession

from app.db.session import engine
from app.modules.logging.models import ErrorLog

async def save_error_log_async(
    exception_type: str,
    message: str,
    tb_text: str,
    path: str,
    method: str,
    user_id: Optional[UUID],
    user_role: Optional[str],
    request_data: dict
):
    async with AsyncSession(engine) as session: 
        log_entry = ErrorLog(
            exception_type=exception_type,
            message=message,
            traceback=tb_text,
            path=path,
            method=method,
            user_id=user_id,
            user_role=user_role,
            request_data=request_data
        )
        session.add(log_entry)
        await session.commit()