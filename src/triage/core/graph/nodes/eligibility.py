from triage.api.deps import get_session_factory
from triage.core.graph.state import AssignmentState
from triage.repositories.team_member_repo import TeamMemberRepository
from triage.repositories.testable_repo import TestableRepository

async def eligibility_node(state: AssignmentState) -> AssignmentState:
    """Hard constraint, deliberately no LLM involved: removes anyone who did
    development work on this testable, and anyone currently marked
    unavailable. This rule is non-negotiable so it stays deterministic and
    independently unit-testable rather than something an LLM could be
    talked out of.
    """
    event = state["event"]
    
    session_factory = get_session_factory()
    async with session_factory() as session:
        testable_repo = TestableRepository(session)
        team_member_repo = TeamMemberRepository(session)

        team_members = await team_member_repo.get_team_members(event.team_id)
        developers = set(await testable_repo.get_developers_for_testable(event.testable_id))

    eligible_members = [m.id for m in team_members if m.id not in developers and m.is_available]
    excluded_members = [m.id for m in team_members if m.id in developers or not m.is_available]

    seniority_by_member = {m.id: m.seniority_years for m in team_members}

    max_seniority = max(seniority_by_member.values(), default=0.0)

    return {
        **state,
        "eligible_members_ids": eligible_members,
        "excluded_members_ids": excluded_members,
        "team_member_seniority": seniority_by_member,
        "max_team_seniority_years": max_seniority
    }
