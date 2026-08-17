from pathlib import Path

from agent_manager.contracts import load_contracts


ROOT = Path(__file__).resolve().parents[1]


def test_agent_cannot_merge_or_deploy() -> None:
    rights = load_contracts(ROOT / "contracts")["decision_rights"]
    approvals = " ".join(rights["human_approval_required"]).lower()
    assert "merge" in approvals
    assert "deploy" in approvals


def test_agent_cannot_weaken_tests() -> None:
    rights = load_contracts(ROOT / "contracts")["decision_rights"]
    approvals = " ".join(rights["human_approval_required"]).lower()
    assert "weaken" in approvals
