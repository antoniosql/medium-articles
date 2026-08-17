# Databricks Data Quality as Code - Solution Skeleton

This repository is a starter skeleton for implementing **Data Quality as Code** on Databricks using:

- **Lakeflow Declarative Pipelines** for data quality enforcement
- **Unity Catalog** as the governance and control plane
- **Reusable quality rules** stored in a governed Delta/Unity Catalog table
- **Event log publishing** for observability
- **Lineage-ready design** for impact analysis

The goal is to separate:

1. **Transformation logic**
2. **Quality policy**
3. **Operational observability**

---

## Repository structure

```text
.
├── .github/
│   └── workflows/
│       └── ci.yml
├── config/
│   ├── app_config.example.yaml
│   └── environments.example.json
├── docs/
│   ├── architecture.md
│   ├── operating-model.md
│   └── rollout-plan.md
├── infra/
│   └── terraform/
│       ├── main.tf
│       ├── variables.tf
│       └── outputs.tf
├── src/
│   ├── common/
│   │   ├── config.py
│   │   ├── logging_utils.py
│   │   └── quality_rules.py
│   ├── observability/
│   │   ├── create_event_log_view.sql
│   │   ├── expectation_metrics.sql
│   │   └── lineage_queries.sql
│   ├── pipelines/
│   │   ├── customers/
│   │   │   ├── pipeline_customers.py
│   │   │   └── expectations_customers.sql
│   │   └── orders/
│   │       ├── pipeline_orders.py
│   │       └── expectations_orders.sql
│   └── sql/
│       ├── create_catalog_structure.sql
│       ├── create_quality_rules_table.sql
│       ├── seed_quality_rules.sql
│       └── quarantine_patterns.sql
├── tests/
│   ├── test_config.py
│   └── test_quality_rules.py
└── requirements.txt
```

---

## Core design principles

### 1. Quality rules are governed assets
Quality rules should not live only inside pipeline code. They are stored in a governed Unity Catalog table and loaded dynamically by tag and action.

### 2. Pipelines stay thin
Each pipeline should focus on ingesting, transforming, and applying reusable rules. It should not hardcode every quality rule forever.

### 3. Observability is built in
The event log should be published and queried to analyze:

- passed records
- failed records
- dropped records
- pipeline update history

### 4. Bronze / Silver / Gold quality contracts
- **Bronze**: preserve raw truth
- **Silver**: clean and standardize with `warn` and `drop`
- **Gold**: enforce stronger contracts with `fail`

---

## Suggested first implementation path

1. Create the catalog, schemas, and quality rules table.
2. Seed a small set of reusable rules.
3. Deploy one Silver pipeline and one Gold pipeline.
4. Publish the event log.
5. Create observability views and dashboards.
6. Expand rule reuse by domain.

---

## Notes

- This repository is intentionally a **starter skeleton**, not a production-ready implementation.
- Adjust syntax and deployment assets to your Databricks edition, workspace conventions, and Lakeflow runtime.
- Comments are written in English on purpose to make the repository reusable across teams.
