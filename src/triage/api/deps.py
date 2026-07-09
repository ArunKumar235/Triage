from typing import AsyncGenerator, Annotated
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncEngine, AsyncSession
from fastapi import Depends, Header, HTTPException, status

from triage.config import Settings, get_settings
from triage.core.kafka.producer import KafkaProducerWrapper
from triage.services.team_member_service import TeamMemberService
from triage.services.team_service import TeamService
from triage.services.testable_service import TestableService

_engine : AsyncEngine | None = None
_session_factory : async_sessionmaker[AsyncSession] | None = None

def init_engine(settings: Settings):
    global _engine, _session_factory
    if _engine is None:
        _engine = create_async_engine(
            settings.database_url, 
            echo=False,
            pool_pre_ping=True
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

async def verify_webhook_signature(
    x_webhook_signature: Annotated[str | None, Header(alias="X-Webhook-Signature")] = None,
    settings: Settings = Depends(get_settings)
) -> None:
    """Shared-secret check for inbound Jira/ServiceNow webhooks.

    Replace with HMAC verification against the provider's actual signing
    scheme once a specific provider integration is wired up.
    """
    if not x_webhook_signature or x_webhook_signature != settings.webhook_shared_secret:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid webhook signature"
        )

async def get_testable_service(
    db: AsyncSession = Depends(get_db)
) -> TestableService:
    return TestableService(db)

async def get_team_service(
    db: AsyncSession = Depends(get_db)
) -> TeamService:
    return TeamService(db)

async def get_team_member_service(
    db: AsyncSession = Depends(get_db)
) -> TeamMemberService:
    return TeamMemberService(db)

async def get_kafka_producer(
    settings: Settings = Depends(get_settings)
) -> KafkaProducerWrapper:
    from triage.core.kafka.producer import get_producer
    
    return get_producer(settings)
