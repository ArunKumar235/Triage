import uuid
from typing import Optional, TypedDict

from triage.models.schemas.assignment_decision import AssignmentDecision
from triage.models.schemas.kafka_events import TestableReadyForTestingEvent


class CandidateContext(TypedDict):
    member_id: uuid.UUID
    seniority_years: float 
    # Range [0.0, 1.0]. 0.0 means at or over max capacity, 1.0 means 100% available capacity.
    capacity_score: float # set by the capacity node
    expertise_score: float # set by the expertise node

class AssignmentState(TypedDict, total=False):
    event: TestableReadyForTestingEvent

    # set by the eligibility node
    eligible_members_ids: list[uuid.UUID]
    excluded_members_ids: list[uuid.UUID]
    team_member_seniority: dict[uuid.UUID, float]
    max_team_seniority_years: float

    # set by capacity_node, filled in further by expertise_node
    candidates: list[CandidateContext]

    # set by constraint_scorer_node
    # ranked_candidates: list[CandidateScore]

    # set by orchestrator_llm_node
    decision: Optional[AssignmentDecision]
