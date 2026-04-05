
from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse

from app.auth.permissions import get_current_user
from app.modules.certificate.schemas import CertificateItem
from app.users.models import User


router = APIRouter(prefix="/api/v1/certificate", tags=["certificate"])

@router.get("/{certificate_id}", response_class=FileResponse)
async def download_certificate(
    certificate_id: str,
    current_user: User = Depends(get_current_user)
    ):
    """
    Endpoint untuk mengunduh file sertifikat tertentu
    """
    raise NotImplementedError

@router.get("/list", response_model=list[CertificateItem])
async def list_earned_certificate(current_user: User = Depends(get_current_user)):
    """
    Endpoint untuk melihat list sertifikat yang bisa diunduh user terlogin
    """
    raise NotImplementedError