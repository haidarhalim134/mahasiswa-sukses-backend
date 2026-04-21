from abc import ABC, abstractmethod
from typing import BinaryIO


class BaseStorage(ABC):

    @abstractmethod
    async def upload(
        self,
        file: BinaryIO,
        bucket: str,
        path: str,
        content_type: str | None = None
    ) -> str:
        pass

    @abstractmethod
    async def download(
        self,
        bucket: str,
        path: str
    ) -> bytes:
        pass

    @abstractmethod
    async def delete(
        self,
        bucket: str,
        path: str
    ) -> None:
        pass

    @abstractmethod
    def get_public_url(
        self,
        bucket: str,
        path: str
    ) -> str:
        pass