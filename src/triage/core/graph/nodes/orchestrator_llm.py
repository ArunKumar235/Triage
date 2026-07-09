from triage.core.graph.state import AssignmentState

async def orchestrator_llm_node(state: AssignmentState) -> AssignmentState:
    """The orchestrator LLM node is the final step in the assignment graph.
    It takes the ranked candidates from the constraint_scorer_node and
    generates a structured decision, which it persists to Postgres. The
    decision is then returned in the state for downstream consumption.
    """
    
    # orchestrator_llm_node yet to be implemented. It depends 
    # on expertise_rag_node and constraint_scorer_node

    return state
