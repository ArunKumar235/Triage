from typing_extensions import Annotated
import uuid
from pydantic import BaseModel, ConfigDict, AwareDatetime, Field

from triage.models.schemas.base.member_availability_base import MemberAvailabilityBase
from triage.models.schemas.base.testable_base import TestableBase
from triage.models.schemas.enums.testable_status import TestableStatus

EventId = Annotated[
    uuid.UUID, 
    Field(
        default_factory=uuid.uuid4, 
        description="Unique identifier for the event"
    )
]

class TestableReadyForTestingEvent(TestableBase):
    model_config = ConfigDict(from_attributes=True) # Enables SQLAlchemy mapping
    
    status: TestableStatus = TestableStatus.UNASSIGNED

    assigned_to: uuid.UUID | None = None

    created_at: AwareDatetime
    updated_at: AwareDatetime

    event_id: EventId

class MemberAvailabilityEvent(MemberAvailabilityBase):
    model_config = ConfigDict(from_attributes=True) # Enables SQLAlchemy mapping
    
    team_id: uuid.UUID

    event_id: EventId

class AssignmentCompletedEvent(BaseModel):
    """Published to `assignment.completed` by both the assignment and
    rebalancing engines, consumed by the notification service. Deliberately
    slim — full reasoning and the ranked candidate list live in Postgres,
    not on the wire."""

    testable_id: str
    team_id: str
    assigned_to: str
    confidence: float
    reasoning: str

    event_id: EventId
