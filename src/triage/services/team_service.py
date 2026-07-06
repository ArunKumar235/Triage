from sqlalchemy.ext.asyncio import AsyncSession

from triage.models.db.team import Team
from triage.models.schemas.webhook_payloads import TeamWebhookPayload
from triage.repositories.team_repo import TeamRepository

class TeamService:
    def __init__(self, db: AsyncSession):
        self._repo = TeamRepository(db)

    async def create_team(self, payload: TeamWebhookPayload) -> Team:
        return await self._repo.create_team(payload)

    async def get_teams(self) -> list[Team]:
        return await self._repo.get_teams()