import uuid
from pydantic import BaseModel, EmailStr, Field

from triage.models.schemas.priority import Priority
from triage.models.schemas.testable_status import TestableStatus
from triage.models.schemas.testable_type import TestableType

class TestableWebhookPayload(BaseModel):
    """Body of the Jira/ServiceNow webhook fired when a story or defect is
    marked ready for testing."""
    testable_id: str = Field(
        min_length=5, 
        max_length=15, 
        pattern=r"^(STRY|DEF)-\d+$",
        description="Unique identifier for the testable, start with STRY | DEF"
    )
    team_id: uuid.UUID
    description: str
    app: str
    feature: str
    testable_type: TestableType
    priority: Priority
    build_points: int = Field(gt=0)
    status: TestableStatus = TestableStatus.UNASSIGNED
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
