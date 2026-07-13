import uuid
from dataclasses import dataclass

from triage.models.schemas.enums.priority import Priority

HIGH_BUILD_POINTS_THRESHOLD = 5
HIGH_PRIORITY_TIERS = {Priority.P0, Priority.P1}

BASE_WEIGHTS = {
    "capacity": 0.40,
    "expertise": 0.35,
    "seniority": 0.25,
}

# Small, additive nudges — these shift the ranking, they don't override it.
BUILD_POINTS_CAPACITY_BOOST = 0.15
PRIORITY_SENIORITY_BOOST = 0.15


def resolve_weights(build_points: int, priority: Priority) -> dict[str, float]:
    """Returns capacity/expertise/seniority weights for one testable, nudged
    by its build points and priority, then renormalized to sum to 1.0.

    Rationale: a high-build-point testable should favor whoever has the
    most free capacity, since a busy senior person is more likely to slip
    the sprint on a large item. A high-priority testable should favor a
    senior person even at some capacity cost, since the cost of a slow or
    wrong review is higher than the cost of a slightly fuller queue.
    """
    weights = dict(BASE_WEIGHTS)

    if build_points >= HIGH_BUILD_POINTS_THRESHOLD:
        weights["capacity"] += BUILD_POINTS_CAPACITY_BOOST
        weights["expertise"] -= BUILD_POINTS_CAPACITY_BOOST / 2
        weights["seniority"] -= BUILD_POINTS_CAPACITY_BOOST / 2

    if priority in HIGH_PRIORITY_TIERS:
        weights["seniority"] += PRIORITY_SENIORITY_BOOST
        weights["capacity"] -= PRIORITY_SENIORITY_BOOST / 2
        weights["expertise"] -= PRIORITY_SENIORITY_BOOST / 2

    total = sum(weights.values())
    return {key: value / total for key, value in weights.items()}


@dataclass
class CandidateScoreInput:
    member_id: uuid.UUID
    seniority_years: float
    capacity_score: float  # 0-1, available_capacity / max_capacity
    expertise_score: float  # 0-1, from the vector store
    max_team_seniority_years: float


@dataclass
class CandidateScore:
    member_id: uuid.UUID
    composite_score: float
    seniority_score: float
    capacity_score: float
    expertise_score: float
    weights_used: dict[str, float]


def normalize_seniority(years: float, max_team_years: float) -> float:
    if max_team_years <= 0:
        return 0.0
    return min(years / max_team_years, 1.0)


def score_candidate(
    candidate: CandidateScoreInput,
    build_points: int,
    priority: Priority,
) -> CandidateScore:
    weights = resolve_weights(build_points, priority)
    seniority_score = normalize_seniority(
        candidate.seniority_years, candidate.max_team_seniority_years
    )

    composite = (
        weights["capacity"] * candidate.capacity_score
        + weights["expertise"] * candidate.expertise_score
        + weights["seniority"] * seniority_score
    )

    return CandidateScore(
        member_id=candidate.member_id,
        composite_score=round(composite, 4),
        seniority_score=round(seniority_score, 4),
        capacity_score=candidate.capacity_score,
        expertise_score=candidate.expertise_score,
        weights_used=weights,
    )


def rank_candidates(
    candidates: list[CandidateScoreInput],
    build_points: int,
    priority: Priority,
) -> list[CandidateScore]:
    """Returns candidates sorted highest composite score first.

    This ranked list — not raw scores — is what the orchestrator LLM
    receives. The LLM validates and narrates this ordering in plain
    English; it does not compute it. If the LLM is ever wrong or
    unavailable, this function alone still produces a defensible,
    unit-testable assignment.
    """
    scored = [score_candidate(candidate, build_points, priority) for candidate in candidates]
    return sorted(scored, key=lambda s: s.composite_score, reverse=True)
