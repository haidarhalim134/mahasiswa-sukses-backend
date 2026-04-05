

from fastapi import APIRouter, File, UploadFile

from app.users.schemas import ProfileUpdate, UserProfile, UserStats


router = APIRouter(prefix="/api/v1/user", tags=["user"])

@router.get("/user/stats", response_model=UserStats)
async def get_user_stats():
    """Returns points, ranking, and current streak seen on the Home screen."""
    raise NotImplementedError

@router.get("/profile", response_model=UserProfile, tags=["Settings"])
async def get_my_profile():
    """Returns the current user's profile info for the 'Pengaturan' screen."""
    raise NotImplementedError

@router.post("/profile", response_model=UserProfile, tags=["Settings"])
async def update_profile(data: ProfileUpdate):
    """Updates profile details from the 'Edit Profile' screen."""
    raise NotImplementedError

@router.post("/profile/avatar", tags=["Settings"])
async def upload_avatar(file: UploadFile = File(...)):
    """Handles 'Ganti Foto Profil' action."""
    raise NotImplementedError

# 3. Preferences & Account
@router.post("/settings/notifications", tags=["Settings"])
async def toggle_notifications(settings: bool):
    """Toggles the 'Notifikasi' switch in the Preferensi section."""
    raise NotImplementedError