"""Offline promotion gate for candidate policies. No online self-modification."""

from dataclasses import dataclass


@dataclass(frozen=True)
class FrozenEvaluation:
    policy_version: str
    cases: int
    serious_miss_rate: float
    unsupported_alerts_per_100_cases: float
    relevant_issue_recall: float


def eligible_for_promotion(incumbent: FrozenEvaluation, candidate: FrozenEvaluation,
                           expert_approved: bool, min_cases: int = 200) -> tuple[bool, str]:
    if not expert_approved:
        return False, "expert approval missing"
    if min(incumbent.cases, candidate.cases) < min_cases:
        return False, "insufficient frozen evaluation cases"
    if candidate.serious_miss_rate > incumbent.serious_miss_rate:
        return False, "serious missed issues worsened"
    if candidate.unsupported_alerts_per_100_cases > incumbent.unsupported_alerts_per_100_cases:
        return False, "unsupported alert burden worsened"
    if candidate.relevant_issue_recall <= incumbent.relevant_issue_recall:
        return False, "no measured recall improvement"
    return True, "passed preliminary aggregate gate; human deployment review still required"
