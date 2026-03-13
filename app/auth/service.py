from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from app.auth.schemas import LoginRequest, RegisterRequest
from app.core.supabase import supabase
from app.users.service import create_user_profile



async def register_user(data: RegisterRequest, db: AsyncSession):

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
    )

    return {"message": "User registered"}


async def login_user(data: LoginRequest):

    res = supabase.auth.sign_in_with_password(
        {
            "email": data.email,
            "password": data.password
        }
    )

    assert res.session != None

    return {
        "access_token": res.session.access_token,
        "refresh_token": res.session.refresh_token,
        "token_type": "bearer"
    }


async def reset_password(email: str):

    supabase.auth.reset_password_for_email(
        email,
        {
            "redirect_to": "http://localhost:8000/api/v1/auth/reset-password-page"
        }
    )

    return {
        "message": "Password reset email sent"
    }