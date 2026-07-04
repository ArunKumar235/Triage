import uuid
from sqlalchemy.orm import Mapped, mapped_column

from triage.models.db.base import Base

class Team(Base):
    __tablename__ = "teams"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)

    name: Mapped[str] = mapped_column(nullable=False, unique=True)