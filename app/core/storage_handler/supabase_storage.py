from .base_handler import BaseStorage
from app.core.supabase import supabase


class SupabaseStorage(BaseStorage):

    async def upload(self, file, bucket: str, path: str, content_type=None) -> str:
        file_bytes = file.read()

        supabase.storage.from_(bucket).upload(
            path,
            file_bytes,
            {"content-type": content_type} if content_type else {}
        )

        return self.get_public_url(bucket, path)

    async def download(self, bucket: str, path: str) -> bytes:
        return supabase.storage.from_(bucket).download(path)

    async def delete(self, bucket: str, path: str) -> None:
        supabase.storage.from_(bucket).remove([path])

    def get_public_url(self, bucket: str, path: str) -> str:
        return supabase.storage.from_(bucket).get_public_url(path)