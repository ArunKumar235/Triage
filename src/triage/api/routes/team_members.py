import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.encoders import jsonable_encoder

from triage.api.deps import get_team_member_service, verify_webhook_signature
from triage.models.schemas.webhook_payloads import TeamMemberWebhookPayload
from triage.services.team_member_service import TeamMemberService

router = APIRouter(prefix="/teams", tags=["team_members"], dependencies=[Depends(verify_webhook_signature)])

@router.post(
    "/{team_id}/members",
    status_code=status.HTTP_201_CREATED
)
async def add_team_member(
    team_id: uuid.UUID,
    payload: TeamMemberWebhookPayload,
    team_member_service: TeamMemberService = Depends(get_team_member_service)
) -> dict:
    """
    Add a member to a team.
    """
    try:
        team_member = await team_member_service.create_team_member(team_id, payload)
        return jsonable_encoder({"status": "created", "team_member": team_member})
    except ValueError as e:
        error_msg = str(e)
        if "already exists" in error_msg:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=error_msg)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=error_msg)

@router.get(
    "/{team_id}/members",
    status_code=status.HTTP_200_OK
)
async def get_team_members(
    team_id: uuid.UUID,
    team_member_service: TeamMemberService = Depends(get_team_member_service)
) -> dict:
    """
    Get all members of a team.
    """
    try:
        team_members = await team_member_service.get_team_members(team_id)
        return jsonable_encoder({"status": "ok", "team_id": team_id, "team_members": team_members})
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
