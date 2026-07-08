import uuid
from sqlalchemy.ext.asyncio import AsyncSession

from triage.models.db.team_member import TeamMember
from triage.models.schemas.webhook_payloads import MemberAvailabilityWebhookPayload, TeamMemberWebhookPayload
from triage.repositories.team_member_repo import TeamMemberRepository

class TeamMemberService:
    def __init__(self, db: AsyncSession):
        self._repo = TeamMemberRepository(db)
    
    async def create_team_member(self, team_id: uuid.UUID, payload: TeamMemberWebhookPayload) -> TeamMember:
        """
        Validates team and developer exist, then creates a new team member.
        """
        if(not await self.team_exists(team_id)):
            raise ValueError("Team not found")

        if(await self._repo.team_member_exists(team_id, payload.email)):
            raise ValueError(f"Team member with email {payload.email} already exists in team {team_id}")
        
        return await self._repo.create_team_member(team_id, payload)

    async def get_team_members(self, team_id: uuid.UUID) -> list[TeamMember]:
        """
        Retrieves all team members for a given team from the database.
        """
        if(not await self.team_exists(team_id)):
            raise ValueError("Team not found")

        return await self._repo.get_team_members(team_id)

    async def team_exists(self, team_id: uuid.UUID):
        """
        Checks if a team exists in the database.
        """
        return await self._repo.team_exists(team_id)
    
    async def update_member_availability(self, team_id: uuid.UUID, payload: MemberAvailabilityWebhookPayload) -> None:
        """
        Updates the availability of a team member.
        """
        if(not await self.team_exists(team_id)):
            raise ValueError("Team not found")

        if(not await self._repo.get_team_member(team_id, payload.member_id)):
            raise ValueError(f"Team member with id {payload.member_id} does not exist in team {team_id}")
        
        await self._repo.update_member_availability(team_id, payload.member_id, payload.is_available)
