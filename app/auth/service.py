from uuid import UUID
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from app.auth.schemas import LoginRequest, LoginResponse, RegisterRequest, TokenRefreshResponse
from app.core.supabase import supabase
from app.users.service import create_user_profile, get_user_by_id



async def register_user(db: AsyncSession, data: RegisterRequest):

    res = supabase.auth.sign_up(
        {
            "email": data.email,
            "password": data.password
        }
    )

    assert res.user != None

    user_id = UUID(res.user.id) 

    await create_user_profile(
        db=db,
        user_id=user_id,
        email=data.email,
        phone_number=data.phone_number,
        nim=data.nim,
        full_name=data.full_name,
        birth_date=data.birth_date,
    )

    return


async def login_user(db: AsyncSession, data: LoginRequest):

    res = supabase.auth.sign_in_with_password(
        {
            "email": data.email,
            "password": data.password
        }
    )

    assert res.session != None

    user_data = await get_user_by_id(db, UUID(res.session.user.id))

    assert user_data != None

    return LoginResponse(
        access_token=res.session.access_token,
        refresh_token=res.session.refresh_token,
        token_type="bearer",
        user=user_data
    )


async def reset_password(email: str):

    supabase.auth.reset_password_for_email(
        email,
        {
            "redirect_to": "http://localhost:8000/api/v1/auth/reset-password-page"
        }
    )

    return

def refresh_access_token(refresh_token):
    session = supabase.auth.refresh_session(refresh_token)

    if not session or not session.session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    return TokenRefreshResponse(
        access_token=session.session.access_token,
        refresh_token=session.session.refresh_token,
    )