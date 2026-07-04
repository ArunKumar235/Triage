import uuid
from typing import Literal
from pydantic import BaseModel, Field

class RankedCandidate(BaseModel):
    member_id: uuid.UUID
    member_display_name: str
    composite_score: float
    capacity_score: float
    expertise_score: float
    seniority_score: float = 0.0

class AssignmentDecision(BaseModel):
    """The orchestrator LLM is constrained to return exactly this shape.

    `ranked_candidates` (not just the top pick) is what makes the
    rebalancing engine cheap: if the top candidate goes on leave, the
    rebalancing graph can fall back to the next entry in this list instead
    of re-running the constraint scorer and the LLM from scratch.
    """

    testable_id: uuid.UUID
    ranked_candidates: list[RankedCandidate]
    top_candidate: str
    confidence: float = Field(ge=0.0, le=1.0)
    primary_rule_applied: Literal["capacity", "expertise", "seniority", "tiebreak"]
    reasoning: str
    flags: list[Literal["low_confidence", "all_at_capacity", "cold_start"]] = Field(
        default_factory=list
    )
