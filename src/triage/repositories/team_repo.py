from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from triage.models.db.team import Team
from triage.models.schemas.webhook_payloads import TeamWebhookPayload

class TeamRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def create_team(self, payload: TeamWebhookPayload) -> Team:
        team = Team(name=payload.name)
        self._session.add(team)
        await self._session.commit()
        await self._session.refresh(team)
        return team

    async def get_teams(self) -> list[Team]:
        query = select(Team).order_by(Team.name.asc())
        result = await self._session.scalars(query)
        return result.all()
