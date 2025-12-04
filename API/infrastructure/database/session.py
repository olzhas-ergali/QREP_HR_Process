from contextvars import ContextVar

from loguru import logger
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

__all__ = ("get_session", "engine", 'db_session', )

from API.config import settings

engine: AsyncEngine = create_async_engine(
    settings.database.url, future=True, pool_pre_ping=True, echo=False
)
SESSION_MAKER = async_sessionmaker(
    engine, expire_on_commit=False, autoflush=False
)

db_session: ContextVar[AsyncSession] = ContextVar('db_session')


async def get_session(_engine: AsyncEngine | None = engine):
    session = SESSION_MAKER()
    return session
