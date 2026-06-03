from uuid import UUID
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from app.auth.schemas import LoginRequest, LoginResponse, RegisterRequest, TokenRefreshResponse
from app.core.supabase import supabase
from app.modules.gamification.services import handle_daily_streak
from app.users.service import create_user_profile, get_user_by_email, get_user_by_id, get_user_by_username



async def register_user(db: AsyncSession, data: RegisterRequest):

    email_used = await get_user_by_email(db, data.email)
    if email_used:
        raise HTTPException(
            status_code=409,
            detail="Email already used"
        )

    username_used = await get_user_by_username(db, data.username)
    if username_used:
        raise HTTPException(
            status_code=409,
            detail="Username already used"
        )
        
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
        username=data.username,
        full_name=data.full_name.strip(),
        birth_date=data.birth_date,
    )

    return


async def login_user(db: AsyncSession, data: LoginRequest):

    email = data.email_or_username
    # username will not contain @, so in case below assume this function is dealing with username
    if "@" not in email:
        user = await get_user_by_username(db, email)
        if not user:
            raise HTTPException(
                status_code=409,
                detail="Invalid credential format"
            )
        email = user.email

    res = supabase.auth.sign_in_with_password(
        {
            "email": email,
            "password": data.password
        }
    )

    if not res.session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credential",
        )

    user_data = await get_user_by_id(db, UUID(res.session.user.id))

    assert user_data != None

    # hook
    await handle_daily_streak(db, user_data)

    return LoginResponse(
        access_token=res.session.access_token,
        refresh_token=res.session.refresh_token,
        token_type="bearer",
        user=user_data
    )


def reset_password(email: str):

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

    # a bit awkward
    return session.user.id, TokenRefreshResponse(
        access_token=session.session.access_token,
        refresh_token=session.session.refresh_token,
    )