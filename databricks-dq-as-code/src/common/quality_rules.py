"""Helpers to load reusable data quality rules from a Unity Catalog table.

This is the core pattern behind 'Data Quality as Code' in this repository:
quality policy is defined in data, not hardcoded in every pipeline.
"""

from __future__ import annotations

from typing import Dict

from pyspark.sql import DataFrame
from pyspark.sql import functions as F



def get_active_rules_df(spark, rules_table: str, tag: str, action: str) -> DataFrame:
    """Return the active rules for a given tag and action.

    Parameters
    ----------
    spark:
        Active Spark session.
    rules_table:
        Fully qualified Unity Catalog table containing reusable rules.
    tag:
        Logical grouping tag, for example 'customers_silver_warn'.
    action:
        Expected rule behavior, for example 'warn', 'drop', or 'fail'.
    """

    return (
        spark.read.table(rules_table)
        .filter(
            (F.col("tag") == tag)
            & (F.col("action") == action)
            & (F.col("active") == F.lit(True))
        )
        .select("rule_name", "constraint_sql")
    )



def load_rules_as_dict(spark, rules_table: str, tag: str, action: str) -> Dict[str, str]:
    """Load active rules into the dictionary shape expected by Lakeflow decorators."""

    rows = get_active_rules_df(spark, rules_table, tag, action).collect()
    return {row["rule_name"]: row["constraint_sql"] for row in rows}
