from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.encoders import jsonable_encoder

from triage.api.deps import get_kafka_producer, get_testable_service, verify_webhook_signature
from triage.core.kafka.producer import KafkaProducerWrapper
from triage.core.kafka.topics import Topics
from triage.models.schemas.kafka_events import TestableReadyForTestingEvent
from triage.models.schemas.webhook_payloads import TestableWebhookPayload
from triage.services.testable_service import TestableService

router = APIRouter(prefix="/testables", tags=["testables"], dependencies=[Depends(verify_webhook_signature)])

@router.post(
    "",
    status_code=status.HTTP_202_ACCEPTED
)
async def upsert_testable(
    payload: TestableWebhookPayload,
    testable_service: TestableService = Depends(get_testable_service)
) -> dict:
    """
    Update or insert the testable payload to database and dev history table, and return 202 Accepted response.
    """
    try:
        testable = await testable_service.upsert_testable(payload)
        return jsonable_encoder({"status": "accepted", "testable": testable})
    except ValueError as e:
        error_msg = str(e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error_msg)

@router.get(
    "",
    status_code=status.HTTP_200_OK
)
async def get_testables(
    testable_service: TestableService = Depends(get_testable_service)
) -> dict:
    """
    Get all testables.
    """
    testables = await testable_service.get_testables()
    return jsonable_encoder({"status": "ok", "testables": testables})

@router.get(
    "/{testable_id}",
    status_code=status.HTTP_200_OK
)
async def get_testable(
    testable_id: str,
    testable_service: TestableService = Depends(get_testable_service)
) -> dict:
    """
    Get a specific testable by ID.
    """
    try:
        testable = await testable_service.get_testable(testable_id)
        return jsonable_encoder({"status": "ok", "testable": testable})
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

@router.publish(
    "/{testable_id}/publish",
    status_code=status.HTTP_202_ACCEPTED
)
async def publish_testable(
    testable_id: str,
    producer: KafkaProducerWrapper = Depends(get_kafka_producer),
    testable_service: TestableService = Depends(get_testable_service)
) -> dict:
    """
    Fired by Jira/ServiceNow when a story or defect is marked ready for testing.

    Publishes onto `testable.created` and returns immediately — the assignment
    consumer does the actual LangGraph work asynchronously.
    """
    try:
        testable = await testable_service.get_testable(testable_id)
        kafka_event = TestableReadyForTestingEvent.model_validate(testable)
        await producer.publish(
            topic=Topics.TESTABLE_READY_FOR_TESTING,
            key=str(kafka_event.testable_id),
            value=kafka_event.model_dump_json()
        )
        return jsonable_encoder({"queued": True, "testable_id": kafka_event.testable_id})
    
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
