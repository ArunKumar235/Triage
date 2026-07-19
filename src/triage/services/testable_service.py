from sqlalchemy.ext.asyncio import AsyncSession

from triage.core.rag.vector_store import get_vector_store
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
        result = await self._repo.upsert_testable(testable)

        vector_store = get_vector_store()

        vector_store.upsert_testable_record(
            testable_id=testable.testable_id,
            team_id=testable.team_id,
            member_ids=testable.developed_by,
            app=testable.app,
            feature=testable.feature,
            description=testable.description
        )
        return result

    async def get_testables(self) -> list[Testable]:
        return await self._repo.get_testables()

    async def get_testable(self, testable_id: str) -> Testable:
        testable = await self._repo.get_testable(testable_id)
        if testable is None:
            raise ValueError(f"Testable with id {testable_id} does not exist")
        return testable