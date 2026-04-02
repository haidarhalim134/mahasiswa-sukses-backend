from fastapi import APIRouter, Depends, Response
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.schemas import RegisterRequest, LoginRequest, ResetPasswordRequest, LoginResponse
from app.auth.service import register_user, login_user, reset_password
from app.db.session import get_db

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@router.post("/register")
async def register(
    data: RegisterRequest,
    db: AsyncSession = Depends(get_db)
):
    await register_user(data, db)
    return Response(status_code=200)


@router.post("/login", response_model=LoginResponse)
async def login(
    data: LoginRequest
):
    return await login_user(data)


@router.post("/reset-password")
async def reset_password_endpoint(
    data: ResetPasswordRequest
):
    await reset_password(data.email)
    return Response(status_code=200)

from fastapi.responses import FileResponse, HTMLResponse

@router.get("/reset-password-page", response_class=HTMLResponse)
async def reset_password_page():
    return FileResponse("./app/templates/reset_password.html")

class UpdatePasswordRequest(BaseModel):
    access_token: str
    password: str


@router.post("/update-password")
async def update_password(data: UpdatePasswordRequest):
    from app.core.supabase import supabase
    supabase.auth.set_session(
        data.access_token,
        data.access_token
    )

    supabase.auth.update_user({
        "password": data.password
    })

    return Response(status_code=200)