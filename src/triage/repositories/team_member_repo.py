import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import EmailStr

from triage.models.db.team import Team
from triage.models.db.team_member import TeamMember
from triage.models.schemas.webhook_payloads import TeamMemberWebhookPayload

class TeamMemberRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def team_exists(self, team_id: uuid.UUID) -> bool:
        """
        Checks if a team exists in the database.
        """
        # session.get
        team = await self._session.get(Team, team_id)
        return team is not None

    async def team_member_exists(self, team_id: uuid.UUID, email: EmailStr) -> bool:
        """
        Checks if a team member exists in the database.
        """
        query = select(TeamMember).where(TeamMember.team_id == team_id, TeamMember.email == email)
        result = await self._session.scalar(query)
        return result is not None

    async def create_team_member(self, team_id: uuid.UUID, payload: TeamMemberWebhookPayload) -> TeamMember:
        """
        Creates a new team member in the database.
        """
        team_member = TeamMember(team_id=team_id)
        self._session.add(team_member)
        team_member.display_name = payload.display_name
        team_member.email = payload.email
        team_member.seniority_years = payload.seniority_years
        team_member.max_capacity_per_sprint = payload.max_capacity_per_sprint
        team_member.is_available = payload.is_available
        
        await self._session.commit()
        await self._session.refresh(team_member)
        return team_member
    
    async def get_team_members(self, team_id: uuid.UUID) -> list[TeamMember]:
        """
        Retrieves all team members for a given team from the database.
        """
        query = select(TeamMember).where(TeamMember.team_id == team_id).order_by(TeamMember.display_name.asc())
        result = await self._session.scalars(query)
        return result.all()

    async def get_team_member(self, team_id: uuid.UUID, member_id: uuid.UUID) -> TeamMember:
        """
        Retrieves a specific team member by ID for a given team from the database.
        """
        query = select(TeamMember).where(TeamMember.team_id == team_id, TeamMember.id == member_id)
        result = await self._session.scalar(query)
        return result

    async def update_member_availability(self, team_id: uuid.UUID, member_id: uuid.UUID, is_available: bool) -> None:
        """
        Updates the availability of a team member.
        """
        team_member = await self.get_team_member(team_id, member_id)
        if team_member is None:
            raise ValueError(f"Team member with id {member_id} does not exist in team {team_id}")
        
        team_member.is_available = is_available
        await self._session.commit()
