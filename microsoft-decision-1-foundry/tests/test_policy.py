import pytest

from frasohome_decision.client import Decision, DecisionAPIError
from frasohome_decision.policy import HUMAN_REVIEW, GatePolicy, TriagePolicy, gate, route


def triage_decision(top: float, blocked: float, frustration: float) -> Decision:
    rest = (1 - top) / 6
    probs = {"entrega": top, **{k: rest for k in ("a", "b", "c", "d", "e", "f")}}
    return Decision(
        raw={
            "answers": {
                "case_type": {"type": "choice", "choice": "entrega", "probabilities": probs},
                "frustration": {"type": "score", "score": frustration},
                "is_blocked": {"type": "noul", "noul": blocked},
            }
        }
    )


@pytest.mark.parametrize(
    ("top", "blocked", "frustration", "expected"),
    [
        (0.95, 0.2, 0.5, "entrega"),
        (0.95, 0.9, 2.4, "entrega:priority"),
        (0.95, 0.9, 1.2, "entrega"),  # blocked but calm
        (0.95, 0.5, 2.8, "entrega"),  # angry but not blocked
        (0.45, 0.9, 2.8, HUMAN_REVIEW),  # unsure about the queue
    ],
)
def test_route(top, blocked, frustration, expected):
    assert route(triage_decision(top, blocked, frustration)) == expected


def test_route_threshold_is_configurable():
    decision = triage_decision(0.55, 0.1, 0.1)
    assert route(decision) == HUMAN_REVIEW
    assert route(decision, TriagePolicy(min_confidence=0.5)) == "entrega"


def test_route_falls_back_to_confidence_when_no_probabilities():
    decision = Decision(
        raw={
            "answers": {
                "case_type": {"choice": "cupon", "confidence": 0.8},
                "frustration": {"score": 0.0},
                "is_blocked": {"noul": 0.0},
            }
        }
    )
    assert route(decision) == "cupon"


SEVERITIES = {"GR-002": "alta", "GR-005": "media", "GR-012": "media"}


def gate_decision(**probabilities: float) -> Decision:
    answers = {k.replace("_", "-"): {"type": "noul", "noul": v} for k, v in probabilities.items()}
    return Decision(raw={"answers": answers})


def test_gate_blocks_on_high_severity():
    result = gate(gate_decision(GR_002=0.6, GR_005=0.1, GR_012=0.1), SEVERITIES)
    assert result.verdict == "BLOCK"
    assert result.blocked_by == [("GR-002", 0.6)]


def test_gate_reviews_on_medium_severity():
    result = gate(gate_decision(GR_002=0.2, GR_005=0.75, GR_012=0.69), SEVERITIES)
    assert result.verdict == "REVIEW"
    assert result.review_for == [("GR-005", 0.75)]


def test_gate_sends_clean_drafts():
    result = gate(gate_decision(GR_002=0.49, GR_005=0.69, GR_012=0.1), SEVERITIES)
    assert result.verdict == "SEND"


def test_gate_policy_is_configurable():
    result = gate(gate_decision(GR_002=0.4), SEVERITIES, GatePolicy(block_at=0.3))
    assert result.verdict == "BLOCK"


def test_decision_rejects_responses_without_answers():
    with pytest.raises(DecisionAPIError):
        Decision(raw={"error": "nope"})


def test_decision_reports_missing_fields():
    decision = Decision(raw={"answers": {"x": {"type": "noul"}}})
    with pytest.raises(DecisionAPIError):
        decision.noul("x")
    with pytest.raises(DecisionAPIError):
        decision.choice("missing")
