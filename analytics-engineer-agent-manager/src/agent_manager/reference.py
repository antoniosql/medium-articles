from __future__ import annotations

import csv
from collections import defaultdict
from datetime import date
from decimal import Decimal
from pathlib import Path


def _month_start(value: str) -> str:
    parsed = date.fromisoformat(value)
    return f"{parsed.year:04d}-{parsed.month:02d}-01"


def calculate_reference_spend(repo_root: Path) -> dict[tuple[str, str], Decimal]:
    seed_dir = repo_root / "dbt_financialhome" / "seeds"

    mapping: dict[str, str] = {}
    with (seed_dir / "category_mapping.csv").open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            mapping[row["raw_category"].strip().lower()] = row["canonical_category"].strip()

    totals: dict[tuple[str, str], Decimal] = defaultdict(lambda: Decimal("0.00"))
    with (seed_dir / "raw_transactions.csv").open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            if row["transaction_type"].strip().lower() != "expense":
                continue
            canonical = mapping[row["raw_category"].strip().lower()]
            amount = abs(Decimal(row["amount_eur"]))
            totals[(_month_start(row["transaction_date"]), canonical)] += amount

    return dict(totals)


def calculate_monthly_totals(repo_root: Path) -> dict[str, Decimal]:
    category_totals = calculate_reference_spend(repo_root)
    monthly: dict[str, Decimal] = defaultdict(lambda: Decimal("0.00"))
    for (month_start, _category), value in category_totals.items():
        monthly[month_start] += value
    return dict(monthly)
