from pathlib import Path

from agent_manager.contracts import load_contracts
from agent_manager.planner import create_deterministic_plan


ROOT = Path(__file__).resolve().parents[1]


def test_plan_ends_with_human_review() -> None:
    contracts = load_contracts(ROOT / "contracts")
    plan = create_deterministic_plan(contracts)
    assert plan.steps[-1].requires_human_approval is True
    assert "review" in plan.steps[-1].name.lower()


def test_plan_contains_validation_before_build() -> None:
    contracts = load_contracts(ROOT / "contracts")
    plan = create_deterministic_plan(contracts)
    names = [step.name.lower() for step in plan.steps]
    assert "validate delegated context" in names[0]
    assert any("run build" in name for name in names)
