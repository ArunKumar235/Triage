from fastapi import APIRouter, Depends, status
from fastapi.encoders import jsonable_encoder

from triage.api.deps import get_team_service, verify_webhook_signature
from triage.models.schemas.webhook_payloads import TeamWebhookPayload
from triage.services.team_service import TeamService

router = APIRouter(prefix="/teams", tags=["teams"], dependencies=[Depends(verify_webhook_signature)])

@router.post(
    "",
    status_code=status.HTTP_201_CREATED
)
async def create_team(
    payload: TeamWebhookPayload,
    team_service: TeamService = Depends(get_team_service)
) -> dict:
    """
    Create a new team.
    """
    team = await team_service.create_team(payload)
    return jsonable_encoder({"status": "created", "team": team})

@router.get(
    "",
    status_code=status.HTTP_200_OK
)
async def get_teams(
    team_service: TeamService = Depends(get_team_service)
) -> dict:
    """
    Get all teams.
    """
    teams = await team_service.get_teams()
    return jsonable_encoder({"status": "ok", "teams": teams})
