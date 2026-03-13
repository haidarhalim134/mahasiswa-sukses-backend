import typing as t
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

engine = create_async_engine(
    str(settings.database_url),
    future=True,
)

AsyncSessionLocal = sessionmaker(
    engine, expire_on_commit=False, class_=AsyncSession
)

# Dependency
async def get_db() -> t.AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session