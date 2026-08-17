# Databricks Quality Delivery Demo

A runnable demo repository that shows **Data Quality as Code** and **Data Quality Delivery** in action.

It includes two layers:

1. **A local runnable demo** using `pandas` so you can see the pattern immediately.
2. **A Databricks-ready implementation** using **Lakeflow Spark Declarative Pipelines** and **Declarative Automation Bundles**.

The goal is to demonstrate this end-to-end flow:

- define reusable rules
- apply them to a dataset
- capture quality metrics
- compare them with a deployment gate
- promote only when the result is acceptable

## Repository structure

```text
.
├── .github/workflows/ci.yml
├── databricks.yml
├── resources/
│   └── customers_quality.pipeline.yml
├── src/
│   ├── databricks_pipeline/
│   │   ├── pipeline.py
│   │   └── rules_module.py
│   └── local_demo/
│       ├── __init__.py
│       ├── engine.py
│       └── cli.py
├── data/
│   ├── customers.csv
│   └── baseline_metrics.json
├── rules/
│   └── quality_rules.yml
├── tests/
│   ├── test_engine.py
│   └── test_cli.py
├── pyproject.toml
└── Makefile
```

## What the local demo does

The local demo simulates a quality-controlled silver table pipeline.

It:

- loads customer data from CSV
- loads reusable rules from YAML
- evaluates each rule against each row
- either **drops** invalid rows or **fails** the run
- writes output metrics to `artifacts/latest_metrics.json`
- compares those metrics to a baseline gate
- returns a non-zero exit code if promotion should be blocked

This gives you a concrete and executable version of the same idea that you would later operationalize in Databricks.

## Quick start

### 1) Create a virtual environment

Using `uv`:

```bash
uv venv
source .venv/bin/activate
uv pip install -e .[dev]
```

Or with `pip`:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
```

### 2) Run tests

```bash
pytest
```

### 3) Run the local demo in drop mode

```bash
python -m local_demo.cli run \
  --data data/customers.csv \
  --rules rules/quality_rules.yml \
  --tag silver_hygiene \
  --mode drop
```

### 4) Inspect the generated metrics

```bash
cat artifacts/latest_metrics.json
```

### 5) Evaluate the promotion gate

```bash
python -m local_demo.cli gate \
  --baseline data/baseline_metrics.json \
  --actual artifacts/latest_metrics.json
```

If the gate passes, promotion is allowed. If it fails, the command exits with code `1`.

## Example output

A successful local run produces:

- `artifacts/clean_customers.csv`
- `artifacts/latest_metrics.json`

The metrics file looks like this:

```json
{
  "dataset": "customers",
  "mode": "drop",
  "input_rows": 8,
  "output_rows": 5,
  "dropped_rows": 3,
  "expectations": {
    "customer_id_not_null": {
      "passed_records": 7,
      "failed_records": 1
    },
    "email_has_at": {
      "passed_records": 7,
      "failed_records": 1
    },
    "country_allowed": {
      "passed_records": 7,
      "failed_records": 1
    }
  }
}
```

## Databricks implementation

The Databricks side of this repo shows the same pattern implemented with:

- `from pyspark import pipelines as dp`
- `@dp.expect_all_or_drop(...)`
- rules externalized into a reusable module
- a bundle project with `dev`, `staging`, and `prod` targets
- production protection using `mode: production` and `run_as`

### Key files

- `databricks.yml`: bundle definition and targets
- `resources/customers_quality.pipeline.yml`: pipeline resource
- `src/databricks_pipeline/rules_module.py`: centralized rules
- `src/databricks_pipeline/pipeline.py`: pipeline logic using expectations

## How to adapt this to a real Databricks workspace

1. Install the Databricks CLI version required by the current docs.
2. Authenticate with your workspace.
3. Update `databricks.yml` with your workspace host and service principal IDs.
4. Update catalog and schema names in the resource YAML.
5. Replace the illustrative CSV source with your bronze source tables or files.
6. Deploy:

```bash
databricks bundle validate
databricks bundle deploy -t dev
databricks bundle deploy -t staging
databricks bundle deploy -t prod
```

## Why the repo is split this way

The **local demo** is meant to be executable everywhere. It helps explain the pattern clearly in a blog post, workshop, or demo.

The **Databricks layer** is meant to show what the same architecture looks like when implemented with the current Databricks model for pipelines and CI/CD.

## Notes

- The original uploaded article is no longer available in the live file-search context, so this repo is built from the sequel architecture and current Databricks documentation rather than by re-reading the expired attachment.
- The Databricks files are intentionally conservative and close to the official docs so they are easy to adapt.

## References

Databricks currently documents that:

- Declarative Automation Bundles are the recommended path for CI/CD and pipeline deployment. citeturn924914search0turn924914search3
- Expectation decorators such as `@dp.expect_all_or_drop(...)` apply data quality constraints to tables and views in pipelines. citeturn436684view0turn436684view1
- Production targets can validate the Git branch and are best protected with service principals through `run_as`. citeturn436684view3turn924914search2
