"""Illustrative centralized rules module for Databricks Lakeflow pipelines.

This file mirrors the pattern recommended in the Databricks expectations guidance:
centralize reusable quality rules and select them by tag.
"""

from __future__ import annotations

from typing import Dict, List


_RULES: List[dict[str, str]] = [
    {
        "name": "customer_id_not_null",
        "constraint": "customer_id IS NOT NULL",
        "tag": "silver_hygiene",
    },
    {
        "name": "email_has_at",
        "constraint": "email LIKE '%@%'",
        "tag": "silver_hygiene",
    },
    {
        "name": "country_allowed",
        "constraint": "country IN ('ES', 'PT', 'FR')",
        "tag": "silver_hygiene",
    },
]


def get_rules(tag: str) -> Dict[str, str]:
    return {
        row["name"]: row["constraint"]
        for row in _RULES
        if row["tag"] == tag
    }
