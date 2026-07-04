import uuid
from typing import Optional
from datetime import UTC, datetime

from sqlalchemy.orm import Mapped, mapped_column, validates
from sqlalchemy import ForeignKey
from sqlalchemy.dialects.postgresql import JSONB

from triage.models.db.base import Base
from triage.models.schemas.assignment_decision import AssignmentDecision
from triage.models.utils.db_types import PydanticJSONB

class AssignmentHistory(Base):
    __tablename__ = "assignment_history"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)

    testable_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("testables.id"), nullable=False)

    team_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("teams.id"), nullable=False)

    assigned_to: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("team_members.id"), nullable=True)

    confidence: Mapped[Optional[float]] = mapped_column(nullable=True)

    reasoning: Mapped[Optional[str]] = mapped_column(nullable=True)

    ranked_candidates_payload: Mapped[Optional[AssignmentDecision]] = mapped_column(
        PydanticJSONB(AssignmentDecision), 
        nullable=True
    )

    overridden_by: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("team_members.id"), nullable=True)

    overridden_reasoning: Mapped[Optional[str]] = mapped_column(nullable=True)

    created_at: Mapped[datetime] = mapped_column(nullable=False, default=datetime.now(UTC))

    @validates("confidence")
    def validate_confidence(self, key, value):
        if value is None:
            return value
        if value < 0.0 or value > 1.0:
            raise ValueError(f"Confidence must be between 0.0 and 1.0. Got: {value}")
        return value