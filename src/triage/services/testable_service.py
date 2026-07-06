import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from triage.models.db.testable import Testable
from triage.models.schemas.webhook_payloads import TestableWebhookPayload
from triage.repositories.testable_repo import TestableRepository

class TestableService:
    def __init__(self, db: AsyncSession):
        self._repo = TestableRepository(db)

    async def upsert_testable(self, testable: TestableWebhookPayload) -> Testable:
        if testable.team_id is None:
            raise ValueError("Team id is required")
        
        await self._repo.team_and_developers_exists(testable.team_id, testable.developed_by)
        return await self._repo.upsert_testable(testable)

    async def get_testables(self) -> list[Testable]:
        return await self._repo.get_testables()

    async def get_testable(self, testable_id: str) -> Testable:
        testable = await self._repo.get_testable(testable_id)
        if testable is None:
            raise ValueError(f"Testable with id {testable_id} does not exist")
        return testable