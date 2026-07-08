import uuid
from pydantic import BaseModel

class MemberAvailabilityBase(BaseModel):
    """Base model for member availability entities."""
    member_id: uuid.UUID
    is_available: bool
