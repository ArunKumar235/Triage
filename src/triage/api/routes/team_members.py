import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.encoders import jsonable_encoder

from triage.api.deps import get_kafka_producer, get_team_member_service, verify_webhook_signature
from triage.core.kafka.producer import KafkaProducerWrapper
from triage.core.kafka.topics import Topics
from triage.models.schemas.kafka_events import MemberAvailabilityEvent
from triage.models.schemas.webhook_payloads import MemberAvailabilityWebhookPayload, TeamMemberWebhookPayload
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
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.post(
    "/{team_id}/members/availability",
    status_code=status.HTTP_202_ACCEPTED,
)
async def update_member_availability(
    team_id: uuid.UUID,
    payload: MemberAvailabilityWebhookPayload,
    producer: KafkaProducerWrapper = Depends(get_kafka_producer),
    team_member_service: TeamMemberService = Depends(get_team_member_service)
):
    """
    Fired by Jira/ServiceNow when a member availability changes.

    Publishes onto `member.availability.changed` and returns immediately, 
    rebalancing consumer does the actual LangGraph work asynchronously.
    """
    try:
        await team_member_service.update_member_availability(team_id, payload)

        if(not payload.is_available):
            # Publish a message to Kafka if the member is not available
            kafka_event = MemberAvailabilityEvent.model_validate(payload)
            kafka_event.team_id = team_id
            await producer.publish(
                topic=Topics.MEMBER_AVAILABILITY_CHANGED,
                key=str(payload.member_id),
                value=kafka_event.model_dump_json()
            )
        return jsonable_encoder({"status": "accepted", "member_id": payload.member_id})

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
