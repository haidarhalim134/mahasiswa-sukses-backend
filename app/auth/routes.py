from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.schemas import RegisterRequest, LoginRequest, ResetPasswordRequest
from app.auth.service import register_user, login_user, reset_password
from app.db.session import get_db

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@router.post("/register")
async def register(
    data: RegisterRequest,
    db: AsyncSession = Depends(get_db)
):
    return await register_user(data, db)


@router.post("/login")
async def login(
    data: LoginRequest
):
    return await login_user(data)


@router.post("/reset-password")
async def reset_password_endpoint(
    data: ResetPasswordRequest
):
    return await reset_password(data.email)