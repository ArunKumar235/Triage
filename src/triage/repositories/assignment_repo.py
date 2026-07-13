import uuid
from sqlalchemy import select

from triage.models.db.assignment_history import AssignmentHistory
from triage.models.schemas.assignment_decision import AssignmentDecision

class AssignmentRepository:
    def __init__(self, session):
        self._session = session

    async def save_decision(self, testable_id: str, team_id: uuid.UUID, decision: AssignmentDecision):
        """Upsert the structured decision. ranked_candidates is stored as
        a pydantic JSONB column, so the rebalancing engine can reuse the
        full ranked list later without re-running the constraint scorer.
        """
        existing = await self._session.execute(
            select(AssignmentHistory).where(AssignmentHistory.testable_id == testable_id)
        )
        record = existing.scalar_one_or_none()

        if record is None:
            record = AssignmentHistory(testable_id=testable_id, team_id=team_id)
            self._session.add(record)

        record.assigned_to = decision.top_candidate_id
        record.reasoning = decision.reasoning
        record.confidence = decision.confidence
        record.ranked_candidates_payload = decision.model_dump(mode='json')
        await self._session.commit()
