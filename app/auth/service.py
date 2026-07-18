import json
from uuid import UUID
from fastapi import HTTPException, Request, status
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from app.auth.schemas import ChangePasswordRequest, LoginRequest, LoginResponse, RegisterRequest, TokenRefreshResponse
from app.core.supabase import supabase
from app.modules.gamification.services import handle_daily_streak
from app.users.models import User
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


async def get_login_data(request: Request) -> LoginRequest:
    content_type = request.headers.get("content-type", "")

    if "application/x-www-form-urlencoded" in content_type or "multipart/form-data" in content_type:
        form_data = await request.form()
    
        email_or_username = form_data.get("username") or form_data.get("email_or_username")
        password = form_data.get("password")
        
        if not email_or_username or not password:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Missing username or password in form data"
            )

        return LoginRequest(email_or_username=email_or_username, password=password)

    try:
        body_bytes = await request.body()
        if not body_bytes:
            raise HTTPException(status_code=422, detail="Signature verification failed: Empty body")
        
        body_json = json.loads(body_bytes)
        return LoginRequest(**body_json)
    except (json.JSONDecodeError, ValidationError) as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid JSON or validation error: {str(e)}"
        )

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
            "redirect_to": "https://mahasiswa-sukses-backend.vercel.app/api/v1/auth/reset-password-page"
        }
    )

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

async def change_user_password(user: User, data: ChangePasswordRequest):
    try:
        supabase.auth.sign_in_with_password(
            {
                "email": user.email,
                "password": data.current_password
            }
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect."
        )

    if data.current_password == data.new_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password should be different from the old password."
        )

    try:
        supabase.auth.update_user({
            "password": data.new_password
        })
    except Exception as exp:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to update password: {str(exp)}"
        )