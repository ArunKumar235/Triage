import uuid
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import ForeignKey

from triage.models.db.base import Base

class TeamMember(Base):
    __tablename__ = "team_members"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)

    team_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("teams.id"), index=True, nullable=False)

    display_name: Mapped[str] = mapped_column(nullable=False)

    email: Mapped[str] = mapped_column(nullable=False, unique=True)

    seniority_years: Mapped[float] = mapped_column(nullable=False, default=0.0)

    max_capacity_per_sprint: Mapped[int] = mapped_column(nullable=False, default=15)

    is_available: Mapped[bool] = mapped_column(nullable=False, default=True)