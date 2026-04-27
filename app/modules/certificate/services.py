from io import BytesIO
from uuid import UUID, uuid4
from fastapi import HTTPException
from httpx import HTTPError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.core.storage_handler import Buckets, get_storage
from app.modules.certificate.models import Certificate
from app.modules.certificate.schemas import CertificateItem, CertificateSource
from playwright.async_api import async_playwright
from io import BytesIO
import os
import subprocess

def ensure_browser_installed():
    cache_path = "/tmp/playwright"
    os.environ["PLAYWRIGHT_BROWSERS_PATH"] = cache_path

    if not os.path.exists(cache_path):
        subprocess.run(["playwright", "install", "chromium"], check=True)

async def generate_certificate(
    db: AsyncSession, 
    awardee_id: UUID, 
    title: str, 
    category: str, 
    source: CertificateSource, 
    source_id: int, 
    template_name: str, 
    replaces: dict
):
    ensure_browser_installed()
    
    with open(f"app/templates/{template_name}", "r", encoding="utf-8") as f:
        svg = f.read()
    
    for key, val in replaces.items():
        svg = svg.replace(key, val)
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body {{ margin: 0; padding: 0; }}
            svg {{ display: block; width: 100%; height: 100%; }}
        </style>
    </head>
    <body>
        {svg}
    </body>
    </html>
    """
    
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        await page.set_content(html_content)
        
        # Generate PDF
        pdf_bytes = await page.pdf(
            format='A4',  # or custom dimensions
            print_background=True,
            margin={'top': '0', 'right': '0', 'bottom': '0', 'left': '0'}
        )
        
        await browser.close()
    
    file = BytesIO(pdf_bytes)
    
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