from triage.core.graph.state import AssignmentState
from triage.core.scoring.constraint_weights import CandidateScoreInput, rank_candidates
from triage.models.schemas.enums.priority import Priority

async def constraint_scorer_node(state: AssignmentState) -> AssignmentState:
    """Wraps scoring/constraint_weights.py into a graph node. This is the 
    deterministic, independently unit-testable layer — the orchestrator
    LLM downstream narrates this ranking, it never recomputes it.
    """
    
    event = state["event"]
    max_seniority = state["max_team_seniority_years"]

    score_inputs = [
        CandidateScoreInput(
            member_id=candidate["member_id"],
            seniority_years=candidate["seniority_years"],
            capacity_score=candidate["capacity_score"],
            expertise_score=candidate["expertise_score"],
            max_team_seniority_years=max_seniority,
        )
        for candidate in state["candidates"]
    ]

    ranked = rank_candidates(
        score_inputs,
        build_points=event.build_points,
        priority=Priority(event.priority),
    )
    
    return {**state, "ranked_candidates": ranked}
