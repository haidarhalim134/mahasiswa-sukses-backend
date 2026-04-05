
from pydantic import BaseModel


class CertificateItem(BaseModel):
    title: str
    url: str