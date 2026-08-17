# The Analytics Engineer Is Becoming an Agent Manager

[![CI](https://github.com/antoniosql/analytics-engineer-agent-manager/actions/workflows/ci.yml/badge.svg)](https://github.com/antoniosql/analytics-engineer-agent-manager/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![dbt](https://img.shields.io/badge/dbt-Core-orange.svg)](https://docs.getdbt.com/)
[![DuckDB](https://img.shields.io/badge/DuckDB-local_OLAP-yellow.svg)](https://duckdb.org/)

A runnable companion repository for the Medium article **[The Analytics Engineer Is Becoming an Agent Manager](https://medium.com/@antoniosql/the-analytics-engineer-is-becoming-an-ai-agent-manager-6be3c1614899?sk=9231139e94456c8e981bc343c78bb6fd)**.

> The point of this project is not to prove that an LLM can generate SQL. It is to show the control system an analytics team needs around any coding agent: intent, context, decision rights, quality gates, evidence, and human accountability.

The demo uses a fictional household-finance domain called **FinancialHome**. An agent is asked to build a governed monthly-spend data product. The repository packages the business rules, source scope, tests, evaluation cases, and approval boundaries that make the task safe enough to delegate.

## What this repository demonstrates

The workflow is deliberately explicit:

```text
Business intent
      ↓
Context bundle ──→ Agent plan ──→ dbt change ──→ Automated gates
      ↑                                           ↓
Decision rights ←──────── Human review ←──── Evidence report
```

An agent may investigate, propose, build, test, and repair. It may **not** redefine a business metric, bypass a failed test, merge to the main branch, or deploy to production without human approval.

## Quick start

### 1. Create a virtual environment

```bash
python -m venv .venv
```

Activate it:

```bash
# macOS / Linux
source .venv/bin/activate

# Windows PowerShell
.venv\Scripts\Activate.ps1
```

### 2. Install the project

```bash
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

### 3. Inspect and validate the agent context

```bash
agent-manager validate
agent-manager plan
```

### 4. Run the complete local demo

```bash
agent-manager demo
```

This command:

1. validates the contracts and decision rights;
2. creates a deterministic agent plan;
3. runs `dbt seed` and `dbt build` against DuckDB;
4. executes business-level evaluation cases;
5. writes a Markdown and JSON evidence report to `outputs/`.

### 5. Prove that the guardrails work

```bash
agent-manager demo --scenario unmapped_category
```

The failure scenario introduces an expense category that has no approved mapping. The build is expected to fail instead of silently assigning the transaction to `Other`.

## Optional LLM planner

The default planner is deterministic so the governance mechanics are visible and the demo works without an API key. An optional OpenAI adapter can replace the planning step while keeping the same contracts and output schema.

```bash
python -m pip install -e ".[llm]"
export OPENAI_API_KEY="..."
export OPENAI_MODEL="your-current-model"
agent-manager plan --planner openai
```

On Windows PowerShell:

```powershell
$env:OPENAI_API_KEY="..."
$env:OPENAI_MODEL="your-current-model"
agent-manager plan --planner openai
```

The model name is intentionally configured through an environment variable rather than hard-coded.

## Repository map

```text
.
├── AGENTS.md                         # Operating instructions for a coding agent
├── contracts/
│   ├── intent_contract.yml           # What outcome is requested
│   ├── decision_rights.yml           # What the agent may and may not do
│   ├── quality_gates.yml             # Required evidence before review
│   └── evaluation_cases.yml          # Business-level acceptance checks
├── dbt_financialhome/
│   ├── seeds/                        # Synthetic FinancialHome source data
│   ├── models/                       # Staging, intermediate, and mart models
│   └── tests/                        # Singular business tests
├── src/agent_manager/                # Control-plane CLI and report generator
├── tests/                            # Tests for the control plane
├── docs/
│   ├── architecture.md               # Design and responsibility boundaries
│   ├── demo-walkthrough.md           # Step-by-step explanation
└── .github/workflows/ci.yml          # The same gates executed in CI
```

## The six management artifacts

| Artifact | Question it answers |
|---|---|
| Intent contract | What business outcome is requested, and what is out of scope? |
| Context bundle | Which sources, definitions, rules, and examples should govern the work? |
| Decision rights | What may the agent do autonomously, and what requires approval? |
| Build gates | Does the project compile, run, test, and reconcile? |
| Evaluation cases | Does the result answer the intended business question correctly? |
| Evidence report | What changed, what passed, what failed, and what must a human review? |

## Why a deterministic planner is included

A reference implementation should distinguish **agent intelligence** from **delivery-system quality**. By keeping the default plan deterministic, you can test the contracts, execution, evidence, and failure behavior independently of model variability. The optional LLM adapter changes only the planner; it does not get to redefine the governance system.

## Useful commands

```bash
make validate       # Validate context contracts
make plan           # Generate a deterministic plan
make test           # Run Python tests
make demo           # Run the successful dbt + DuckDB scenario
make demo-fail      # Run the expected guardrail failure
make clean          # Remove local build artifacts
```


## Scope and limitations

This is an educational reference architecture, not a production autonomous-development platform. A production implementation would also need isolated execution, secrets management, branch protection, policy enforcement, artifact signing, audit retention, identity-aware tool permissions, cost controls, and organization-specific security review.

## License

MIT. See [LICENSE](LICENSE).
