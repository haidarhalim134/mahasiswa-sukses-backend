from .base_handler import BaseStorage
from app.core.supabase import get_supabase


class SupabaseStorage(BaseStorage):

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.supabase = get_supabase()


    async def upload(self, file, bucket: str, path: str, content_type=None) -> str:
        file_bytes = file.read()

        file_options = {"upsert": "true"}
        if content_type:
            file_options["content-type"] = content_type

        self.supabase.storage.from_(bucket).upload(
            path,
            file_bytes,
            file_options=file_options
        )

        return self.get_public_url(bucket, path)

    async def download(self, bucket: str, path: str) -> bytes:
        return self.supabase.storage.from_(bucket).download(path)

    async def delete(self, bucket: str, path: str) -> None:
        self.supabase.storage.from_(bucket).remove([path])

    def get_public_url(self, bucket: str, path: str) -> str:
        return self.supabase.storage.from_(bucket).get_public_url(path)