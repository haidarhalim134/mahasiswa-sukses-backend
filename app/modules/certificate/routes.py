
from fastapi import APIRouter
from fastapi.responses import FileResponse

from app.modules.certificate.schemas import CertificateItem


router = APIRouter(prefix="/api/v1/certificate", tags=["certificate"])

@router.get("/{certificate_id}", response_class=FileResponse)
async def download_certificate(certificate_id: str):
    """
    Endpoint untuk mengunduh file sertifikat tertentu
    """
    raise NotImplementedError

@router.get("/list", response_model=list[CertificateItem])
async def list_earned_certificate():
    """
    Endpoint untuk melihat list sertifikat yang bisa diunduh user terlogin
    """
    raise NotImplementedError