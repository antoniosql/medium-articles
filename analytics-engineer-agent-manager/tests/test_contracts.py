from pathlib import Path

from agent_manager.contracts import has_errors, load_contracts, validate_contracts


ROOT = Path(__file__).resolve().parents[1]


def test_repository_contracts_are_valid() -> None:
    contracts = load_contracts(ROOT / "contracts")
    issues = validate_contracts(contracts)
    assert not has_errors(issues), issues


def test_evaluation_model_matches_intent() -> None:
    contracts = load_contracts(ROOT / "contracts")
    intended = contracts["intent"]["required_grain"]["model"]
    evaluated = contracts["evaluation_cases"]["output_model"]
    assert evaluated == intended
