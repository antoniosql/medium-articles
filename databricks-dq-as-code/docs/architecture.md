# Architecture Overview

## Logical flow

1. Raw data lands in **Bronze**.
2. Lakeflow pipelines read Bronze tables.
3. Reusable expectations are loaded from a **Unity Catalog rules table**.
4. Silver pipelines apply `warn` and `drop` logic.
5. Gold pipelines apply stricter `fail` logic.
6. Pipeline event logs are published for observability.
7. Lineage and event log queries are used for impact analysis.

## Main components

- **Unity Catalog**: governance layer for tables, rules, permissions, and lineage
- **Lakeflow Declarative Pipelines**: quality enforcement layer
- **Quality Rules Table**: reusable repository of business rules
- **Event Log Views**: operational monitoring surface
- **Downstream BI / AI / data products**: trusted consumers of curated outputs
