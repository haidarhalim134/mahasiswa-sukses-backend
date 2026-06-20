from enum import Enum
from app.core.config import settings
from .base_handler import BaseStorage


def get_storage() -> BaseStorage:
    # NOTE: always true for now until migration
    if settings.app_env == "serverless":
        from .supabase_storage import SupabaseStorage
        return SupabaseStorage()

    from .local_handler import LocalStorage
    return LocalStorage()

class Buckets(Enum):
    AVATAR = "avatar"
    CERTIFICATE = 'certificate'