import os
import aiofiles
from pathlib import Path
from .base_handler import BaseStorage


class LocalStorage(BaseStorage):

    def __init__(self, base_path: str = "storage"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

    def _full_path(self, bucket: str, path: str) -> Path:
        return self.base_path / bucket / path

    async def upload(self, file, bucket: str, path: str, content_type=None) -> str:
        full_path = self._full_path(bucket, path)
        full_path.parent.mkdir(parents=True, exist_ok=True)

        file_content = file.read()
        async with aiofiles.open(full_path, "wb") as f:
            await f.write(file_content)

        return path

    async def download(self, bucket: str, path: str) -> bytes:
        full_path = self._full_path(bucket, path)

        async with aiofiles.open(full_path, "rb") as f:
            return await f.read()

    async def delete(self, bucket: str, path: str) -> None:
        full_path = self._full_path(bucket, path)
        if full_path.exists():
            os.remove(full_path)

    def get_public_url(self, bucket: str, path: str) -> str:
        return f"/storage/{bucket}/{path}"