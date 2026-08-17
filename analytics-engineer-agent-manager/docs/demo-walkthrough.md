# Demo walkthrough

## The delegated request

The fictional request sounds simple:

> Build a monthly view of household spend by category and compare it with budget.

That sentence leaves critical questions unanswered. Does spend include transfers? Are source amounts signed? What defines a month? Can an unknown category become `Other`? Is positive variance good or bad? Who may change a category definition?

The repository answers those questions before an agent writes SQL.

## 1. Intent contract

`contracts/intent_contract.yml` defines the outcome, source scope, grain, measures, business rules, deliverables, acceptance criteria, and out-of-scope work.

## 2. Decision rights

`contracts/decision_rights.yml` separates autonomous work from approval-gated and prohibited actions. The agent can build and test a branch. It cannot redefine a metric, weaken a test, merge, or deploy.

## 3. Agent instructions

`AGENTS.md` describes the operating sequence and the priority of context sources. It also defines stop conditions so ambiguity becomes a visible handoff rather than an invisible guess.

## 4. dbt implementation

The data flow is:

```text
CSV seeds
   ↓
stg_transactions + reference staging models
   ↓
int_transactions_enriched
   ↓
fct_monthly_spend + dim_category
```

The mart exposes actual spend, budget, variance, percentage variance, transaction count, and budget status.

## 5. Technical gates

The dbt project checks:

- source identifiers and accepted values;
- explicit category mapping for every expense;
- one row per month and category;
- non-negative published spend;
- reconciliation between source expenses and the published mart.

## 6. Business evaluations

`contracts/evaluation_cases.yml` contains examples that a business reviewer can understand, including:

- January spend equals EUR 1,925 and excludes salary;
- February spend equals EUR 2,292;
- March insurance is EUR 270 over budget;
- January telecommunications spend equals EUR 85;
- total published spend reconciles to source expenses.

These cases are not a replacement for dbt tests. They answer a different question: **does the delivered model behave as the business intent expects?**

## 7. Expected failure

Run:

```bash
agent-manager demo --scenario unmapped_category
```

The alternate seed includes `Experimental Subscription`, which has no approved category mapping. The singular dbt test must fail. That is a successful demonstration of the governance system: the agent is blocked instead of inventing a category or hiding the row.

## 8. Evidence and review

Every demo writes:

```text
outputs/agent_run_report.md
outputs/agent_run_report.json
```

The report records context validation, plan steps, commands, evaluation results, and the final blocking reason. It ends with a required human-review checklist and never authorizes its own merge.
