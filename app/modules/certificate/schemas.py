
from enum import Enum
from pydantic import BaseModel

class CertificateSource(str, Enum):
    QUIZ = 'quiz'

class CertificateItem(BaseModel):
    title: str
    category: str
    certificate_id: str