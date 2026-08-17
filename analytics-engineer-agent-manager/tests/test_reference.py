from decimal import Decimal
from pathlib import Path

from agent_manager.reference import calculate_monthly_totals, calculate_reference_spend


ROOT = Path(__file__).resolve().parents[1]


def test_reference_monthly_totals() -> None:
    totals = calculate_monthly_totals(ROOT)
    assert totals["2026-01-01"] == Decimal("1925.00")
    assert totals["2026-02-01"] == Decimal("2292.00")
    assert totals["2026-03-01"] == Decimal("2741.00")


def test_reference_category_values() -> None:
    totals = calculate_reference_spend(ROOT)
    assert totals[("2026-01-01", "Telecommunications")] == Decimal("85.00")
    assert totals[("2026-03-01", "Insurance")] == Decimal("420.00")
