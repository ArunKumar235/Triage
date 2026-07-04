import uuid
from enum import Enum
from datetime import datetime, UTC
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import ForeignKey, Enum as SQLEnum

from triage.models.db.base import Base
from triage.models.schemas.testable_type import TestableType
from triage.models.schemas.priority import Priority
from triage.models.schemas.testable_status import TestableStatus

class Testable(Base):
    __tablename__ = "testables"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)

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

    created_at: Mapped[datetime] = mapped_column(nullable=False, default=datetime.now(UTC))