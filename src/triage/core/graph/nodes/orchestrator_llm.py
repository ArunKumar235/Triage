import uuid
from langchain_ollama import ChatOllama
from langchain_core.output_parsers import PydanticOutputParser

from triage.config import get_settings
from triage.core.graph.state import AssignmentState
from triage.models.schemas.assignment_decision import AssignmentDecision, RankedCandidate


ORCHESTRATOR_SYSTEM_PROMPT = """You are a QA resource allocator.

You are given a pre-computed, weighted ranking of eligible candidates. 

Your only job is to review the ranked list of candidates and provide a human readable explanation of the top pick.

Do not recompute the scores — trust them unless something looks clearly wrong
(for example a near-tie that should be broken differently), in which case
explain the tiebreak you'd apply instead.

Expertise score could be 0 if the candidate has no relevant experience, 
so don't assume that a 0 expertise score is an error. 

Identify which factor most drove the top pick: capacity, expertise,
seniority, or a tiebreak between close scores. Keep the reasoning to 2-3
sentences, written for a scrum master rather than an engineer.

IMPORTANT: 
- You must respond with ONLY valid JSON matching the requested schema. Do not include markdown formatting, conversational text, or any preamble/postamble.
- Populate testable_id, top_candidate_id, and ranked_candidates EXACTLY with the data provided in the user prompt to ensure valid output.

{format_instructions}
"""

def _format_candidates_for_prompt(ranked_candidates) -> str:
    lines = []
    for rank, candidate in enumerate(ranked_candidates, start=1):
        lines.append(
            f"{rank}. {candidate.member_id} — composite {candidate.composite_score:.2f} "
            f"(capacity {candidate.capacity_score:.2f}, expertise {candidate.expertise_score:.2f}, "
            f"seniority {candidate.seniority_score:.2f})"
        )
    return "\n".join(lines)

async def orchestrator_llm_node(state: AssignmentState) -> AssignmentState:
    """The orchestrator LLM node is the final step in the assignment graph.
    It takes the ranked candidates from the constraint_scorer_node and
    generates a structured decision, which it persists to Postgres. The
    decision is then returned in the state for downstream consumption.
    """
    
    event = state["event"]
    ranked = state["ranked_candidates"]

    if not ranked:
        decision = AssignmentDecision(
            testable_id=event.testable_id,
            ranked_candidates=[],
            top_candidate_id=uuid.UUID(int=0),
            confidence=0.0,
            primary_rule_applied="tiebreak",
            reasoning="No eligible candidates were available for this testable.",
            flags=["all_at_capacity"],
        )
        return {**state, "decision": decision}

    settings = get_settings()
    llm = ChatOllama(
        model=settings.orchestrator_model,
        temperature=0,
        format="json",
    )
    parser = PydanticOutputParser(pydantic_object=AssignmentDecision)

    prompt = (
        f"Testable: {event.testable_id} ({event.app} / {event.feature})\n"
        f"Priority: {event.priority}, Build points: {event.build_points}\n\n"
        f"Ranked candidates:\n{_format_candidates_for_prompt(ranked)}\n\n"
        f"Top-ranked candidate by composite score: {ranked[0].member_id}"
    )

    system_prompt = ORCHESTRATOR_SYSTEM_PROMPT.format(
        format_instructions=parser.get_format_instructions()
    )

    response = await llm.ainvoke(
        [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ]
    )
    
    decision: AssignmentDecision = parser.parse(response.content)

    # The LLM doesn't reliably echo back exact IDs and numeric scores for
    # fields that are already known data — overwrite those rather than
    # trusting free-form generation for anything that isn't the reasoning
    # text or the rule classification.
    decision.testable_id = event.testable_id
    decision.ranked_candidates = [
        RankedCandidate(
            member_id=c.member_id,
            composite_score=c.composite_score,
            capacity_score=c.capacity_score,
            expertise_score=c.expertise_score,
            seniority_score=c.seniority_score,
        )
        for c in ranked
    ]
    if decision.top_candidate_id not in {c.member_id for c in ranked}:
        decision.top_candidate_id = ranked[0].member_id
        decision.flags = list(set(decision.flags + ["low_confidence"]))

    return {**state, "decision": decision}
