from uuid import UUID
from fastapi import APIRouter, File, HTTPException, Response, UploadFile, Depends
import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.permissions import get_current_user
from app.db.session import get_db
from app.users.models import User
from app.users.schemas import ProfileUpdate, SettingsUpdate, UserProfile, UserStats
from app.users.service import get_user_by_id


router = APIRouter(prefix="/api/v1/user", tags=["user"])


@router.get("/stats", response_model=UserStats)
async def get_user_stats(
    current_user: User = Depends(get_current_user),
):
    """Endpoint untuk mengambil data stats homescreen"""
    raise NotImplementedError


@router.get("/profile", response_model=UserProfile)
async def get_my_profile(
    current_user: User = Depends(get_current_user),
):
    """Endpoint untuk mengambil data profile user"""
    raise NotImplementedError


@router.post("/profile", response_model=UserProfile)
async def update_profile(
    data: ProfileUpdate,
    current_user: User = Depends(get_current_user),
):
    """Endpoint untuk mengupdate data profile user"""
    raise NotImplementedError


@router.post("/profile/avatar")
async def upload_avatar(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
):
    """Endpoint untuk memperbarui avatar user"""
    raise NotImplementedError


# 3. Preferences & Account
@router.post("/settings")
async def update_settings(
    settings: SettingsUpdate,
    current_user: User = Depends(get_current_user),
):
    """Toggles the 'Notifikasi' switch in the Preferensi section."""
    raise NotImplementedError

@router.get(
    "/avatar/{user_id}",
    responses = {
        200: {
            "content": {"image/png": {}}
        }
    },
    response_class=Response
)
async def get_avatar(
    user_id: UUID, 
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Endpoint untuk mengambil avatar user tertentu"""
        # TODO: replace with your actual DB fetch
    user = await get_user_by_id(db, user_id)  # implement this

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if not user.full_name:
        raise HTTPException(status_code=400, detail="User full name not available")

    # Build ui-avatars URL
    # Example: https://ui-avatars.com/api/?name=John+Doe&format=png
    name_query = user.full_name.replace(" ", "+")
    url = f"https://ui-avatars.com/api/?name={name_query}&format=png"

    async with httpx.AsyncClient() as client:
        resp = await client.get(url)

    if resp.status_code != 200:
        raise HTTPException(status_code=502, detail="Failed to fetch avatar")

    return Response(content=resp.content, media_type="image/png")