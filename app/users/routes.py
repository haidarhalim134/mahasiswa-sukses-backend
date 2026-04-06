from uuid import UUID
from fastapi import APIRouter, File, Response, UploadFile, Depends

from app.auth.permissions import get_current_user
from app.users.models import User
from app.users.schemas import ProfileUpdate, SettingsUpdate, UserProfile, UserStats


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
):
    """Endpoint untuk mengambil avatar user tertentu"""
    raise NotImplementedError