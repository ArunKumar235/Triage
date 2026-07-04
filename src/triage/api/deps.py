from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncEngine, AsyncSession
from triage.config import Settings

_engine : AsyncEngine | None = None
_session_factory : async_sessionmaker[AsyncSession] | None = None

def init_engine(settings: Settings):
    global _engine, _session_factory
    if _engine is None:
        _engine = create_async_engine(
            settings.database_url, 
            echo=True
            ,pool_pre_ping=True
        )
        _session_factory = async_sessionmaker(
            _engine, 
            expire_on_commit=False
        )

def get_engine():
    if _engine is None:
        raise RuntimeError("Database not initialized")
    return _engine

def get_session_factory():
    if _session_factory is None:
        raise RuntimeError("Database not initialized")
    return _session_factory

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    session_factory = get_session_factory()
    async with session_factory() as session:
        yield session