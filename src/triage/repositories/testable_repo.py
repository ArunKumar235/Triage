import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import delete, select, func

from triage.models.schemas.enums.role import Role
from triage.models.schemas.enums.testable_status import TestableStatus
from triage.models.schemas.webhook_payloads import TestableWebhookPayload
from triage.models.db.testable import Testable
from triage.models.db.dev_history import DevHistory
from triage.models.db.team import Team
from triage.models.db.team_member import TeamMember

class TestableRepository:
    def __init__(self, session: AsyncSession):
        self._session = session
    
    async def upsert_testable(self, testable: TestableWebhookPayload) -> Testable:
        """
        This performs an upsert: if a Testable with the given id exists it is
        updated, otherwise a new row is inserted. DevHistory entries for the
        testable are replaced with the provided developed_by list.
        """
        existing = await self._session.get(Testable, testable.testable_id)

        if existing is None:
            existing = Testable(id=testable.testable_id)
            self._session.add(existing)
    
        existing.team_id = testable.team_id
        existing.description = testable.description
        existing.app = testable.app
        existing.feature = testable.feature
        existing.testable_type = testable.testable_type
        existing.priority = testable.priority
        existing.build_points = testable.build_points
        if existing.status is None:
            existing.status = TestableStatus.UNASSIGNED
        

        await self._session.execute(
            delete(DevHistory).where(DevHistory.testable_id == testable.testable_id)
        )
        
        for developer_id in testable.developed_by:
            dev_history_entry = DevHistory(
                testable_id=testable.testable_id,
                team_member_id=developer_id,
                role=Role.DEVELOPER,
            )
            self._session.add(dev_history_entry)

        await self._session.commit()
        await self._session.refresh(existing)
        return existing

    async def team_and_developers_exists(self, team_id: str, developed_by: list) -> None:
        """
        Validates that the team exists and all developers are part of that team.
        """
        # Ensure referenced team exists
        team = await self._session.get(Team, team_id)
        if team is None:
            raise ValueError(f"Team with id {team_id} does not exist")
        
        # Ensure referenced developers exist and belong to the team
        if developed_by:
            query = select(TeamMember).where(
                TeamMember.team_id == team_id,
                TeamMember.id.in_(developed_by)
            )
            existing_developers = await self._session.scalars(query)
            existing_developers_list = existing_developers.all()
            existing_developer_ids = {dev.id for dev in existing_developers_list}
            missing_developer_ids = set(developed_by) - existing_developer_ids
            if missing_developer_ids:
                raise ValueError(f"Developers with ids {missing_developer_ids} do not exist")

    async def get_testables(self) -> list[Testable]:
        """
        Retrieves all testables from the database.
        """
        query = select(Testable).order_by(Testable.id.asc())
        result = await self._session.scalars(query)
        return result.all()
    
    async def get_testable(self, testable_id: str) -> Testable:
        """
        Retrieves a specific testable by ID from the database.
        """
        testable = await self._session.get(Testable, testable_id)
        return testable
    
    async def get_developers_for_testable(self, testable_id: str) -> list[uuid.UUID]:
        """
        Member IDs who did development work on this testable — used by
        the eligibility agent to exclude them from testing their own work.
        """
        query = (
            select(DevHistory.team_member_id)
            .where(
                DevHistory.testable_id == testable_id,
                DevHistory.role == Role.DEVELOPER
            )
        )
        result = await self._session.scalars(query)
        return result.all()
    
    async def get_pending_build_points(self, member_id: uuid.UUID) -> float:
        """
        Retrieves the total build points of testables that are not yet 
        completed, where this team member was the developer.
        """
        query = (
            select(func.sum(Testable.build_points))
            .join(DevHistory, DevHistory.testable_id == Testable.id)
            .where(
                DevHistory.team_member_id == member_id,
                DevHistory.role == Role.DEVELOPER,
                Testable.status != TestableStatus.COMPLETED
            )
        )

        result = await self._session.scalar(query)
        
        # scalar() returns None if there are no matching rows, so we fallback to 0.0
        return float(result or 0.0)

    async def assign_tester_to_testable(self, testable_id: str, tester_id: uuid.UUID) -> None:
        """
        Assigns a tester to a specific testable.
        """
        testable = await self._session.get(Testable, testable_id)
        if testable is None:
            raise ValueError(f"Testable with id {testable_id} does not exist")
        
        testable.assigned_to = tester_id
        testable.status = TestableStatus.ASSIGNED

        # update the DevHistory to reflect the tester assignment
        dev_history_entry = DevHistory(
            testable_id=testable_id,
            team_member_id=tester_id,
            role=Role.TESTER,
        )
        self._session.add(dev_history_entry)

        await self._session.commit()
