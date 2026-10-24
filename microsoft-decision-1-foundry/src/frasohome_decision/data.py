"""Loaders for the FraSoHome sample data in ./data."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

DATA_DIR = Path("data")
TICKETS_CSV = DATA_DIR / "support_tickets.csv"
RULES_CSV = DATA_DIR / "brand_guardrails.csv"
DRAFT_JSON = DATA_DIR / "sample_draft.json"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def load_tickets(path: Path = TICKETS_CSV) -> list[dict[str, str]]:
    return read_csv(path)


def load_rules(path: Path = RULES_CSV) -> list[dict[str, str]]:
    return read_csv(path)


def load_draft(path: Path = DRAFT_JSON) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))
