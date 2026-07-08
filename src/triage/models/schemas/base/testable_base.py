import uuid
from pydantic import AliasChoices, BaseModel, Field

from triage.models.schemas.enums.priority import Priority
from triage.models.schemas.enums.testable_type import TestableType

class TestableBase(BaseModel):
    """Base model for testable entities."""
    testable_id: str = Field(
        min_length=5, 
        max_length=15, 
        pattern=r"^(STRY|DEF)-\d+$",
        description="Unique identifier for the testable, start with STRY | DEF",
        validation_alias=AliasChoices('testable_id', 'id')
    )
    team_id: uuid.UUID
    description: str
    app: str
    feature: str
    testable_type: TestableType
    priority: Priority
    build_points: int = Field(gt=0)
