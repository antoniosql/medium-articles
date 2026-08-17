"""Example customer pipelines using reusable expectations.

This file demonstrates the separation between:
- ingestion/transformation logic
- centralized quality rules
- contract severity by dataset layer
"""

from __future__ import annotations

from pyspark import pipelines as dp

from src.common.quality_rules import load_rules_as_dict


RULES_TABLE = "main.governance.quality_rules"


@dp.table(name="customers_silver")
@dp.expect_all(load_rules_as_dict(spark, RULES_TABLE, "customers_silver_warn", "warn"))
@dp.expect_all_or_drop(load_rules_as_dict(spark, RULES_TABLE, "customers_silver_drop", "drop"))
def customers_silver():
    """Build the Silver customer table from raw Bronze input.

    Silver is usually the best place for standardization and hygiene rules.
    """

    return (
        spark.readStream.table("main.bronze.customers_raw")
        .select("customer_id", "email", "country", "updated_at")
    )


@dp.table(name="customers_gold")
@dp.expect_all_or_fail(load_rules_as_dict(spark, RULES_TABLE, "customers_gold_fail", "fail"))
def customers_gold():
    """Build the Gold customer table from the curated Silver dataset.

    Gold is where stricter business contracts typically belong.
    """

    return spark.read.table("customers_silver")
