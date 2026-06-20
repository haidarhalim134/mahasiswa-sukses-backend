import hashlib
import io
from typing import Annotated
from PIL import Image
from uuid import UUID
from fastapi import APIRouter, File, HTTPException, Request, Response, UploadFile, Depends
import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.permissions import get_current_user, get_current_user_id
from app.core.storage_handler import Buckets, get_storage
from app.db.session import get_db
from app.users.models import User
from app.users.schemas import ProfileUpdate, SettingsUpdate, UserProfile, UserStats
from app.users.service import get_user_by_id, update_profile_data, update_user_setting, user_to_private_view


router = APIRouter(prefix="/api/v1/user", tags=["user"])

HTTP_401_UNAUTHORIZED = {"description": "Missing or invalid authentication token"}
HTTP_404_NOT_FOUND = {"description": "Resource not found"}

@router.get(
    "/profile", 
    response_model=UserProfile,
    responses={
        200: {"description": "Profile data successfully retrieved."},
        401: HTTP_401_UNAUTHORIZED
    }
)
async def get_my_profile(
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Endpoint untuk mengambil data profile user"""
    return user_to_private_view(current_user)


@router.post(
    "/profile", 
    response_model=UserProfile,
    responses={
        200: {"description": "Profile data successfully updated."},
        400: {"description": "Invalid input data format."},
        401: HTTP_401_UNAUTHORIZED
    }
)
async def update_profile(
    data: ProfileUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """Endpoint untuk mengupdate data profile user. Set None/null untuk field yang tidak akan di update"""
    return await update_profile_data(db, current_user, data)


@router.post(
    "/profile/avatar",
    status_code=204,
    responses={
        204: {"description": "Avatar successfully processed and uploaded. No content returned."},
        400: {"description": "Uploaded file is not a valid image format."},
        401: HTTP_401_UNAUTHORIZED
    }
)
async def upload_avatar(
    current_user: Annotated[User, Depends(get_current_user)],
    file: Annotated[UploadFile, File(...)],
):
    """Endpoint untuk memperbarui avatar user. Menerima berbagai format gambar (`*.jpeg`, `*.png`, `*.webp`, dll.)"""
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

    # # delete old image (try to atleast)
    # try:
    #     await storage.delete(
    #         bucket=Buckets.AVATAR.value,
    #         path=path
    #     )
    # except:
    #     pass


@router.post(
    "/settings",
    responses={
        200: {"description": "Settings successfully updated."},
        400: {"description": "Invalid settings input data."},
        401: HTTP_401_UNAUTHORIZED
    }
)
async def update_settings(
    data: SettingsUpdate,
    current_user_id: Annotated[UUID, Depends(get_current_user_id)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """Endpoint untuk memperbarui setting profile mahasiswa. Set None/null untuk field yang tidak akan di update"""
    return await update_user_setting(db, current_user_id, data)

@router.get(
    "/avatar/{user_id}",
    response_class=Response,
    responses={
        200: {
            "content": {"image/webp": {}},
            "description": "Returns the user avatar or a fallback generated avatar in WebP format."
        },
        304: {
            "description": "Not Modified. Client's cached avatar is up to date (If cache mechanism is enabled)."
        },
        400: {
            "description": "Avatar missing from storage and user's full name is unavailable to generate placeholder."
        },
        404: HTTP_404_NOT_FOUND,
        502: {
            "description": "Bad Gateway. Failed to fetch fallback placeholder avatar from external API."
        }
    }
)
async def get_avatar(
    user_id: UUID, 
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """Endpoint untuk mengambil avatar user tertentu"""
    user = await get_user_by_id(db, user_id)

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    storage = get_storage()
    path = f"{user_id}.webp"

    data = None

    try:
        data = await storage.download(Buckets.AVATAR.value, path)
    except Exception:
        if not user.full_name:
            raise HTTPException(status_code=400, detail="User full name not available")

        name_query = user.full_name.replace(" ", "+")
        url = f"https://ui-avatars.com/api/?name={name_query}&format=webp"

        async with httpx.AsyncClient() as client:
            resp = await client.get(url)

        if resp.status_code != 200:
            raise HTTPException(status_code=502, detail="Failed to fetch avatar")

        data = resp.content

    # cache stuff
    etag = hashlib.md5(data).hexdigest()
    if request.headers.get("if-none-match") == etag:
        return Response(status_code=304)

    return Response(
        content=data,
        media_type="image/webp",
        headers={
            "ETag": etag,
            "Cache-Control": "public, s-maxage=5, stale-while-revalidate=3600"
        }
    )