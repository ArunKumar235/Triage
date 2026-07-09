from triage.api.deps import get_session_factory
from triage.core.graph.state import AssignmentState, CandidateContext
from triage.repositories.team_member_repo import TeamMemberRepository
from triage.repositories.testable_repo import TestableRepository

async def capacity_node(state: AssignmentState) -> AssignmentState:
    """Computes a 0-1 capacity score per eligible candidate:
    available_capacity / max_capacity. A busy candidate scores low without
    being excluded outright — the constraint scorer decides how much that
    should matter relative to expertise and seniority for this testable.
    """

    candidates: list[CandidateContext] = []

    session_factory = get_session_factory()
    async with session_factory() as session:
        team_member_repo = TeamMemberRepository(session)
        testable_repo = TestableRepository(session)

        for member_id in state["eligible_members_ids"]:
            max_capacity = await team_member_repo.get_max_capacity(member_id)
            pending = await testable_repo.get_pending_build_points(member_id)

            available = max(max_capacity - pending, 0)
            # print(f"Member {member_id} has max_capacity={max_capacity}, pending={pending}, available={available}")
            capacity_score = (available / max_capacity) if max_capacity > 0 else 0.0

            candidate = CandidateContext(
                member_id=member_id,
                seniority_years=state["team_member_seniority"].get(member_id, 0.0),
                capacity_score=round(capacity_score,4),
                expertise_score=0.0  # Placeholder, will be set by the expertise node
            )
            candidates.append(candidate)

    return {
        **state,
        "candidates": candidates
    }
