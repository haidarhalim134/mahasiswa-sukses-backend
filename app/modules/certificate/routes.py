
from fastapi import APIRouter, Depends, Response
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.permissions import get_current_user
from app.db.session import get_db
from app.modules.certificate.schemas import CertificateItem
from app.modules.certificate.services import download, get_user_certificate
from app.users.models import User


router = APIRouter(prefix="/api/v1/certificate", tags=["certificate"])

@router.get(
    "/{certificate_id}", 
    responses={
        200: {
            "content": {"application/pdf": {}},
            "description": "Returns a PDF file"
        }
    },
    response_class=Response
)
async def download_certificate(
    certificate_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
    ):
    """
    Endpoint untuk mengunduh file sertifikat tertentu
    """
    file = await download(db, current_user.id, certificate_id)
    return Response(content=file)

@router.get("/list", response_model=list[CertificateItem])
async def list_earned_certificate(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
    ):
    """
    Endpoint untuk melihat list sertifikat yang bisa diunduh user terlogin
    """
    return await get_user_certificate(db, current_user.id)