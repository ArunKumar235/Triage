from triage.core.graph.state import AssignmentState

async def expertise_rag_node(state: AssignmentState) -> AssignmentState:
    """Scores each candidate's expertise via the team-filtered RAG layer.
    The testable's app + feature + description is embedded as the query; 
    each candidate's score is their best-matching historical assignment's 
    similarity. Stays scoped to this testable's team_id, cross-team 
    escalation widens the filter upstream of this node, not here.
    """

    # RAG layer, yet to be implemented. For now, expertise_score remains 0.0
    # as set by the capacity node.

    return state
