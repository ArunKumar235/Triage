from triage.core.graph.state import AssignmentState
from triage.core.rag.vector_store import get_vector_store

async def expertise_rag_node(state: AssignmentState) -> AssignmentState:
    """Scores each candidate's expertise via the team-filtered RAG layer.
    The testable's app + feature + description is embedded as the query; 
    each candidate's score is their best-matching historical assignment's 
    similarity. Stays scoped to this testable's team_id, cross-team 
    escalation widens the filter upstream of this node, not here.
    """

    event = state["event"]
    vector_store = get_vector_store()

    candidate_ids = [candidate["member_id"] for candidate in state["candidates"]]

    scores = vector_store.expertise_score_per_member(
        team_ids=[event.team_id],
        candidate_member_ids=candidate_ids,
        app=event.app,
        feature=event.feature,
        description=event.description,
    )

    updated_candidates = [
        {**candidate, "expertise_score": round(scores.get(candidate["member_id"], 0.0), 4)}
        for candidate in state["candidates"]
    ]

    return {**state, "candidates": updated_candidates}
