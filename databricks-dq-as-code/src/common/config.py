"""Configuration helpers for the Data Quality as Code skeleton.

This module intentionally keeps configuration access simple.
In a real project, you might replace this with environment-aware
configuration loaders, secret scopes, or deployment-managed settings.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import yaml


@dataclass
class PlatformConfig:
    """Represents the minimum platform configuration required by the project."""

    catalog: str
    governance_schema: str
    observability_schema: str
    bronze_schema: str
    silver_schema: str
    gold_schema: str
    rules_table: str



def load_config(path: str | Path) -> PlatformConfig:
    """Load configuration from a YAML file.

    Parameters
    ----------
    path:
        Path to the YAML configuration file.

    Returns
    -------
    PlatformConfig
        Parsed configuration object.
    """

    with open(path, "r", encoding="utf-8") as handle:
        raw = yaml.safe_load(handle)

    return PlatformConfig(
        catalog=raw["platform"]["catalog"],
        governance_schema=raw["platform"]["governance_schema"],
        observability_schema=raw["platform"]["observability_schema"],
        bronze_schema=raw["platform"]["bronze_schema"],
        silver_schema=raw["platform"]["silver_schema"],
        gold_schema=raw["platform"]["gold_schema"],
        rules_table=raw["quality"]["rules_table"],
    )
