"""Illustrative Databricks Lakeflow Spark Declarative Pipeline.

To run this in Databricks, adapt the bronze source path or source table, and deploy it
through the bundle included in this repository.
"""

from __future__ import annotations

from pyspark import pipelines as dp
from pyspark.sql import functions as F

from rules_module import get_rules


@dp.table(name="customers_bronze")
def customers_bronze():
    return (
        spark.read.format("csv")
        .option("header", "true")
        .load("/Volumes/main/demo/raw/customers.csv")
    )


@dp.table(name="customers_silver")
@dp.expect_all_or_drop(get_rules("silver_hygiene"))
def customers_silver():
    return (
        spark.read.table("customers_bronze")
        .withColumn("customer_id", F.col("customer_id").cast("int"))
        .withColumn("email", F.trim(F.col("email")))
        .withColumn("country", F.upper(F.trim(F.col("country"))))
        .withColumn("name", F.initcap(F.trim(F.col("name"))))
    )
