import typing as t
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool
from app.core.config import settings

engine_kwargs = {
    "future": True,
    "connect_args": {
        "prepared_statement_cache_size": 0,
        "statement_cache_size": 0,
    }
}

if settings.app_env == "vps":
    engine_kwargs = {
        **engine_kwargs,
        "pool_size": 15, 
        "max_overflow": 5,
        "pool_timeout": 15,
        "pool_recycle": 1800,
        "pool_pre_ping": True
    }
elif settings.app_env == "serverless":
    # quick hit and go connection
    engine_kwargs = ({
        **engine_kwargs,
        "poolclass": NullPool,
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