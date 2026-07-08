import uuid
from pydantic import BaseModel, EmailStr, Field

from triage.models.schemas.base.member_availability_base import MemberAvailabilityBase
from triage.models.schemas.base.testable_base import TestableBase

class TestableWebhookPayload(TestableBase):
    """Body of the Jira/ServiceNow webhook fired when a story or defect is created or updated."""
    
    developed_by: list[uuid.UUID] = Field(
        default_factory=list, 
        description="List of developer IDs who worked on this testable"
    )

class TeamWebhookPayload(BaseModel):
    """Body of the Jira/ServiceNow webhook fired when a team is created or updated."""
    name: str

class TeamMemberWebhookPayload(BaseModel):
    """Body of the Jira/ServiceNow webhook fired when a team member is created or updated."""
    display_name: str
    email: EmailStr
    seniority_years: float = Field(ge=0.0)
    max_capacity_per_sprint: int = Field(gt=0)
    is_available: bool = True

class MemberAvailabilityWebhookPayload(MemberAvailabilityBase):
    """Body fired when a team member's availability changes mid-sprint, 
    triggering the rebalancing graph."""
    pass
