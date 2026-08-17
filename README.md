# Medium Articles

Companion repositories for my Medium articles, consolidated into a single monorepo.
Each folder is a self-contained project with its own README, dependencies, and tests.

## Projects

| Folder | What it is |
| --- | --- |
| [databricks-dq-as-code](databricks-dq-as-code/) | Starter skeleton for **Data Quality as Code** on Databricks: Lakeflow Declarative Pipelines, Unity Catalog governance, reusable quality rules in a governed Delta table, and event-log observability. |
| [databricks-quality-delivery-demo](databricks-quality-delivery-demo/) | Runnable demo of **Data Quality Delivery**: define rules, apply them to a dataset, capture metrics, compare against a deployment gate, and promote only when the result is acceptable. Local `pandas` demo plus a Databricks Asset Bundle implementation. |
| [analytics-engineer-agent-manager](analytics-engineer-agent-manager/) | Companion to *[The Analytics Engineer Is Becoming an Agent Manager](https://medium.com/@antoniosql/the-analytics-engineer-is-becoming-an-ai-agent-manager-6be3c1614899?sk=9231139e94456c8e981bc343c78bb6fd)*. A dbt + DuckDB project showing the control system a team needs around a coding agent: intent, context bundles, decision rights, quality gates, and evidence. |
| [ai-agent-unit-economics-calculator](ai-agent-unit-economics-calculator/) | Companion to *Your AI Agent Is Not Expensive Because of Tokens*. An Excel model for evaluating AI agents by **cost per successful outcome** rather than token spend alone. |

## Working with a project

Each project keeps its own setup instructions. Start from its README:

```bash
cd <project-folder>
cat README.md
```


