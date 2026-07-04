import uuid
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import ForeignKey, Enum as SQLEnum

from triage.models.db.base import Base
from triage.models.schemas.role import Role

class DevHistory(Base):
    __tablename__ = "dev_history"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)

    testable_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("testables.id"), nullable=False)

    team_member_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("team_members.id"), nullable=False)

    role: Mapped[Role] = mapped_column(
        SQLEnum(
            Role,
            name="role_enum",
            native_enum=True, 
            values_callable=lambda e: [item.value for item in e]
        ),
        nullable=False
    )