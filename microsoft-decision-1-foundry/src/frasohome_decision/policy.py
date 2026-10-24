"""Deterministic policies. The model answers questions; code decides what happens."""

from __future__ import annotations

from dataclasses import dataclass, field

from frasohome_decision.client import Decision

HUMAN_REVIEW = "human_review"


@dataclass(frozen=True)
class TriagePolicy:
    min_confidence: float = 0.6  # below this top probability, a person decides
    blocked_threshold: float = 0.8  # noul probability that the customer is blocked
    frustration_threshold: float = 2.0  # 0..3 scale; 2 = "Frustrated"


DEFAULT_TRIAGE_POLICY = TriagePolicy()


def route(decision: Decision, policy: TriagePolicy = DEFAULT_TRIAGE_POLICY) -> str:
    """Queue for a ticket: '<case_type>', '<case_type>:priority' or 'human_review'."""
    top = decision.top_probability("case_type")
    if top is None or top < policy.min_confidence:
        return HUMAN_REVIEW
    case_type = decision.choice("case_type")
    blocked = decision.noul("is_blocked")
    frustration = decision.score("frustration")
    if blocked >= policy.blocked_threshold and frustration >= policy.frustration_threshold:
        return f"{case_type}:priority"
    return case_type


@dataclass(frozen=True)
class GatePolicy:
    """pi-warden style split: high severity blocks, medium sends to review."""

    block_at: float = 0.5  # for rules with severity 'alta'
    review_at: float = 0.7  # for rules with severity 'media' (or any other)


DEFAULT_GATE_POLICY = GatePolicy()


@dataclass
class GateVerdict:
    verdict: str  # SEND | REVIEW | BLOCK
    blocked_by: list[tuple[str, float]] = field(default_factory=list)
    review_for: list[tuple[str, float]] = field(default_factory=list)
    probabilities: dict[str, float] = field(default_factory=dict)


def gate(
    decision: Decision, severities: dict[str, str], policy: GatePolicy = DEFAULT_GATE_POLICY
) -> GateVerdict:
    result = GateVerdict(verdict="SEND")
    for rule_id in decision.answers:
        p = decision.noul(rule_id)
        result.probabilities[rule_id] = p
        if severities.get(rule_id) == "alta":
            if p >= policy.block_at:
                result.blocked_by.append((rule_id, round(p, 3)))
        elif p >= policy.review_at:
            result.review_for.append((rule_id, round(p, 3)))
    if result.blocked_by:
        result.verdict = "BLOCK"
    elif result.review_for:
        result.verdict = "REVIEW"
    return result
