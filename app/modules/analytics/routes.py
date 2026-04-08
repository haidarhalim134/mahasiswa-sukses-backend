from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.permissions import get_current_user


router = APIRouter(prefix="/api/v1/analytics", tags=["analytics"])