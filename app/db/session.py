import typing as t
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool
from app.core.config import settings

# Configuration logic based on environment
engine_kwargs = {
    "future": True,
}

if settings.app_env == "serverless":
    # Serverless (Vercel) Optimization:
    # No local pooling (let Supavisor handle it) and disable statement cache
    engine_kwargs = ({
        **engine_kwargs,
        "poolclass": NullPool,
        "connect_args": {
            "prepared_statement_cache_size": 0,
            "statement_cache_size": 0,
        }
    })

engine = create_async_engine(
    str(settings.database_url),
    **engine_kwargs
)

AsyncSessionLocal = sessionmaker(
    engine, expire_on_commit=False, class_=AsyncSession
)

# Dependency
async def get_db() -> t.AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session