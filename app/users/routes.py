import io
from PIL import Image
from uuid import UUID
from fastapi import APIRouter, File, HTTPException, Response, UploadFile, Depends
import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.permissions import get_current_user
from app.core.storage_handler import Buckets, get_storage
from app.db.session import get_db
from app.users.models import User
from app.users.schemas import ProfileUpdate, SettingsUpdate, UserProfile, UserStats
from app.users.service import get_user_by_id


router = APIRouter(prefix="/api/v1/user", tags=["user"])


# @router.get("/stats", response_model=UserStats)
# async def get_user_stats(
#     current_user: User = Depends(get_current_user),
# ):
#     """Endpoint untuk mengambil data stats homescreen"""
#     raise NotImplementedError


@router.get("/profile", response_model=UserProfile)
async def get_my_profile(
    current_user: User = Depends(get_current_user),
):
    """Endpoint untuk mengambil data profile user"""
    return UserProfile(
        id=current_user.id,
        email=current_user.email,
        full_name=current_user.full_name,
        phone_number=current_user.phone_number,
        nim=current_user.nim,
        birth_date=current_user.birth_date
    )


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
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(400, "File must be an image")

    storage = get_storage()

    contents = await file.read()
    image = Image.open(io.BytesIO(contents))

    if image.mode in ("RGBA", "P"):
        image = image.convert("RGB")

    image.thumbnail((512, 512))

    buffer = io.BytesIO()
    image.save(buffer, format="WEBP", quality=80, optimize=True)
    buffer.seek(0)

    path = f"{current_user.id}.webp"

    await storage.upload(
        file=buffer,
        bucket=Buckets.AVATAR.value,
        path=path,
        content_type="image/webp"
    )

    # delete old image (try to atleast)
    try:
        await storage.delete(
            bucket=Buckets.AVATAR.value,
            path=path
        )
    except:
        pass


# 3. Preferences & Account
@router.post("/settings")
async def update_settings(
    settings: SettingsUpdate,
    current_user: User = Depends(get_current_user),
):
    """Endpoint untuk memperbarui setting profile mahasiswa"""
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
    db: AsyncSession = Depends(get_db)
):
    """Endpoint untuk mengambil avatar user tertentu"""
    user = await get_user_by_id(db, user_id)

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    storage = get_storage()

    path = f"{user_id}.webp"

    try:
        data = await storage.download(Buckets.AVATAR.value, path)
        return Response(content=data, media_type="image/webp")
    except Exception:
        pass

    if not user.full_name:
        raise HTTPException(status_code=400, detail="User full name not available")

    name_query = user.full_name.replace(" ", "+")
    url = f"https://ui-avatars.com/api/?name={name_query}&format=webp"

    async with httpx.AsyncClient() as client:
        resp = await client.get(url)

    if resp.status_code != 200:
        raise HTTPException(status_code=502, detail="Failed to fetch avatar")

    return Response(content=resp.content, media_type="image/webp")