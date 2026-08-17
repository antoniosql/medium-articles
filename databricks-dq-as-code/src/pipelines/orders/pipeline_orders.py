"""Example orders pipeline using the same reusable rules pattern.

The point is not the specific business logic here.
The point is showing that the same framework can scale to many domains.
"""

from __future__ import annotations

from pyspark import pipelines as dp

from src.common.quality_rules import load_rules_as_dict


RULES_TABLE = "main.governance.quality_rules"


@dp.table(name="orders_silver")
@dp.expect_all(load_rules_as_dict(spark, RULES_TABLE, "orders_silver_warn", "warn"))
@dp.expect_all_or_drop(load_rules_as_dict(spark, RULES_TABLE, "orders_silver_drop", "drop"))
def orders_silver():
    """Curate raw orders with reusable quality rules."""

    return (
        spark.readStream.table("main.bronze.orders_raw")
        .select("order_id", "customer_id", "amount", "currency", "order_ts")
    )
