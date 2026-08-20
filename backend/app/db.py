from __future__ import annotations

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from .config import settings

engine = create_async_engine(settings.database_url, echo=False)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False)


async def init_models() -> None:
    from . import models

    async with engine.begin() as conn:
        await conn.run_sync(models.Base.metadata.create_all)
