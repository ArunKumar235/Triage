from langgraph.graph import StateGraph, START, END
from langchain_core.runnables import RunnableConfig

from triage.core.graph.nodes.orchestrator_llm import orchestrator_llm_node
from triage.models.schemas.kafka_events import TestableReadyForTestingEvent
from triage.models.schemas.assignment_decision import AssignmentDecision
from triage.core.graph.state import AssignmentState
from triage.core.graph.nodes.eligibility import eligibility_node
from triage.core.graph.nodes.capacity import capacity_node
from triage.core.graph.nodes.expertise_rag import expertise_rag_node
from triage.core.graph.nodes.constraint_scorer import constraint_scorer_node

def build_assignment_graph():
    graph = StateGraph(AssignmentState)

    graph.add_node("eligibility", eligibility_node)
    graph.add_node("capacity", capacity_node)
    graph.add_node("expertise", expertise_rag_node)
    graph.add_node("constraint_scorer", constraint_scorer_node)
    graph.add_node("orchestrator_llm", orchestrator_llm_node)

    graph.add_edge(START, "eligibility")
    graph.add_edge("eligibility", "capacity")
    graph.add_edge("capacity", "expertise")
    graph.add_edge("expertise", "constraint_scorer")
    graph.add_edge("constraint_scorer", "orchestrator_llm")
    graph.add_edge("orchestrator_llm", END)

    return graph.compile()


_compiled_graph = None

def _get_compiled_graph():
    global _compiled_graph
    if _compiled_graph is None:
            _compiled_graph = build_assignment_graph()
    return _compiled_graph


async def run_assignment_graph(event: TestableReadyForTestingEvent) -> AssignmentDecision:
    """Entry point used by the Kafka assignment consumer. Runs the full
    eligibility -> capacity -> expertise -> constraint_scorer -> orchestrator
    pipeline for one testable and returns the structured decision, which the
    orchestrator node has already persisted to Postgres by the time this
    returns.
    """
    compiled_graph = _get_compiled_graph()
    initial_state: AssignmentState = {"event": event}

    config = RunnableConfig(
        run_name=f"Assignment Workflow: {event.testable_id}",
        metadata={"testable_id": event.testable_id},
        tags=["assignment_graph"]
    )
    final_state = await compiled_graph.ainvoke(initial_state, config=config)

    decision = final_state.get("decision")
    if decision is None:
        raise RuntimeError(
            f"Assignment graph completed without producing a decision for {event.testable_id}"
        )

    return decision
