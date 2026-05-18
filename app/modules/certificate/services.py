from io import BytesIO
from uuid import UUID, uuid4
import aiofiles
from fastapi import HTTPException
from httpx import HTTPError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.core.config import settings
from app.core.storage_handler import Buckets, get_storage
from app.modules.certificate.models import Certificate
from app.modules.certificate.schemas import CertificateItem, CertificateSource
import httpx
import asyncio
# import cairosvg

async def generate_certificate(db: AsyncSession, awardee_id: UUID, title: str, category: str, source: CertificateSource, source_id: int, template_name: str, replaces: dict):
    async with aiofiles.open(f"app/templates/{template_name}", "r", encoding="utf-8") as f:
        svg = await f.read()

    for key, val in replaces.items():
        svg = svg.replace(key, val)

    # TODO: move to hybrid vps and vercel deployment handler as well maybe?
    async with httpx.AsyncClient() as client:
            headers = {"Authorization": f"Bearer {settings.cloudconvert_api_key}"}
            
            payload = {
                "tasks": {
                    "import-svg": {
                        "operation": "import/raw",
                        "file": svg,
                        "filename": "certificate.svg"
                    },
                    "convert-to-pdf": {
                        "operation": "convert",
                        "input": "import-svg",
                        "output_format": "pdf"
                    },
                    "export-pdf": {
                        "operation": "export/url",
                        "input": "convert-to-pdf"
                    }
                }
            }

            job_res = await client.post("https://api.cloudconvert.com/v2/jobs", json=payload, headers=headers)
            job_res.raise_for_status()
            job_data = job_res.json()["data"]
            job_id = job_data["id"]

            pdf_url = None
            while not pdf_url:
                await asyncio.sleep(1) # Wait 1 second between checks
                status_res = await client.get(f"https://api.cloudconvert.com/v2/jobs/{job_id}", headers=headers)
                status_data = status_res.json()["data"]

                if status_data["status"] == "finished":
                    export_task = next(t for t in status_data["tasks"] if t["name"] == "export-pdf")
                    pdf_url = export_task["result"]["files"][0]["url"]
                elif status_data["status"] == "error":
                    raise Exception(f"CloudConvert Job Failed: {status_data}")

            download_res = await client.get(pdf_url)
            download_res.raise_for_status()
            file = BytesIO(download_res.content)

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