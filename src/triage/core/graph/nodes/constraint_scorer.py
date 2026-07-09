from triage.core.graph.state import AssignmentState

async def constraint_scorer_node(state: AssignmentState) -> AssignmentState:
    """Wraps scoring/constraint_weights.py into a graph node. This is the 
    deterministic, independently unit-testable layer — the orchestrator
    LLM downstream narrates this ranking, it never recomputes it.
    """
    
    # constraint_weights.py yet to be implemented. For now,
    # constraint_scorer_node returns state unchanged

    return state
