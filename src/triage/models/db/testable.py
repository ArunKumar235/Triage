import uuid
from datetime import datetime, UTC
from sqlalchemy.orm import Mapped, mapped_column, validates
from sqlalchemy import ForeignKey, Enum as SQLEnum, String, DateTime

from triage.models.db.base import Base
from triage.models.schemas.enums.testable_type import TestableType
from triage.models.schemas.enums.priority import Priority
from triage.models.schemas.enums.testable_status import TestableStatus

class Testable(Base):
    __tablename__ = "testables"

    id: Mapped[str] = mapped_column(
        String(15), 
        primary_key=True, 
        comment="Unique identifier for the testable, start with STRY | DEF"
    )

    team_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("teams.id"), nullable=False)

    description: Mapped[str] = mapped_column(nullable=False)

    app: Mapped[str] = mapped_column(nullable=False)

    feature: Mapped[str] = mapped_column(nullable=False)

    testable_type: Mapped[TestableType] = mapped_column(
        SQLEnum(
            TestableType,
            name="testable_type_enum",
            native_enum=True,
            values_callable=lambda e: [item.value for item in e]
        ),
        nullable=False
    )

    priority: Mapped[Priority] = mapped_column(
        SQLEnum(
            Priority,
            name="priority_enum",
            native_enum=True,
            values_callable=lambda e: [item.value for item in e]
        ),
        nullable=False
    )

    build_points: Mapped[int] = mapped_column(nullable=False)

    status: Mapped[TestableStatus] = mapped_column(
        SQLEnum(
            TestableStatus,
            name="status_enum",
            native_enum=True,
            values_callable=lambda e: [item.value for item in e]
        ),
        nullable=False
    )

    assigned_to: Mapped[uuid.UUID] = mapped_column(ForeignKey("team_members.id"), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False, 
        default=lambda: datetime.now(UTC)
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False, 
        default=lambda: datetime.now(UTC), 
        onupdate=lambda: datetime.now(UTC)
    )

    @validates("id")
    def validate_id(self, key: str, value: str) -> str:
        value = value.strip()
        if not (value.startswith("STRY-") or value.startswith("DEF-")):
            raise ValueError("id must start with STRY- or DEF-")
        if len(value) > 15:
            raise ValueError("id must be less than 15 characters")
        return value