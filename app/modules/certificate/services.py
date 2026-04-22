from io import BytesIO
from uuid import UUID, uuid4
import cairosvg
from fastapi import HTTPException
from httpx import HTTPError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.core.storage_handler import Buckets, get_storage
from app.modules.certificate.models import Certificate
from app.modules.certificate.schemas import CertificateItem, CertificateSource

async def generate_certificate(db: AsyncSession, awardee_id: UUID, title: str, category: str, source: CertificateSource, source_id: int, template_name: str, replaces: dict):
    with open(f"app/templates/{template_name}", "r", encoding="utf-8") as f:
        svg = f.read()

    for key, val in replaces.items():
        svg = svg.replace(key, val)

    file = cairosvg.svg2pdf(bytestring=svg.encode("utf-8"))
    file = BytesIO(file)

    storage = get_storage()

    id: str = str(uuid4())
    path = f"{id}.pdf"
    await storage.upload(file, Buckets.CERTIFICATE.value, path)

    certificate = Certificate(
        id=id,
        user_id=awardee_id,
        source=source,
        source_id=source_id,
        title=title,
        category=category
    )
    db.add(certificate)
    await db.commit()

    return id


async def get_user_certificate(db: AsyncSession, user_id: UUID):
    stmt = select(Certificate).where(Certificate.user_id == user_id)

    result = await db.execute(stmt)
    certificates = result.scalars().all()

    return [CertificateItem(
        title=x.title,
        category=x.category,
        certificate_id=x.id
    ) for x in certificates]

async def download(db: AsyncSession, user_id: UUID, certificate_id: str):
    # ensure this function only care about the currently logged in user certificate
    stmt = select(Certificate).where(Certificate.user_id == user_id, Certificate.id == certificate_id)
    result = await db.execute(stmt)
    certificates = result.scalars().first()
    if not certificates:
        raise HTTPException(404, "Certificate not found")

    storage = get_storage()

    path = f"{certificate_id}.pdf"
    data = await storage.download(Buckets.CERTIFICATE.value, path)
    return data