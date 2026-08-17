from __future__ import annotations

from typing import Any

from .models import PlanStep, RunPlan


def create_deterministic_plan(contracts: dict[str, dict[str, Any]]) -> RunPlan:
    intent = contracts["intent"]
    change_id = str(intent["change_id"])
    title = str(intent["title"])

    assumptions = [
        "The supplied CSV seeds are the only approved source data for this demo.",
        "The canonical category mapping is business-owned and must not be changed by the agent.",
        "The target relation is built in the local DuckDB main schema.",
        "A human reviewer remains accountable for semantic approval, merge, and deployment.",
    ]

    unresolved_questions = [
        "Should annual insurance be normalized for management reporting in a later change?",
        "Should categories with zero actual spend remain visible because they have a budget?",
    ]

    steps = [
        PlanStep(
            step_id="STEP-01",
            name="Validate delegated context",
            purpose="Confirm that intent, decision rights, gates, and evaluations are complete and consistent.",
            expected_files=[
                "contracts/intent_contract.yml",
                "contracts/decision_rights.yml",
                "contracts/quality_gates.yml",
                "contracts/evaluation_cases.yml",
            ],
            commands=["agent-manager validate"],
        ),
        PlanStep(
            step_id="STEP-02",
            name="Inspect source and semantic scope",
            purpose="Confirm source fields, category mappings, budget grain, and existing dbt conventions.",
            expected_files=[
                "dbt_financialhome/seeds/*.csv",
                "dbt_financialhome/models/**/*.sql",
                "dbt_financialhome/models/**/*.yml",
            ],
        ),
        PlanStep(
            step_id="STEP-03",
            name="Build the governed transformation",
            purpose="Create the smallest dbt change that implements the approved monthly-spend contract.",
            expected_files=[
                "dbt_financialhome/models/staging/stg_transactions.sql",
                "dbt_financialhome/models/intermediate/int_transactions_enriched.sql",
                "dbt_financialhome/models/marts/finance/fct_monthly_spend.sql",
            ],
        ),
        PlanStep(
            step_id="STEP-04",
            name="Add technical and business tests",
            purpose="Encode grain, mapping, non-negative spend, and reconciliation requirements as executable gates.",
            expected_files=[
                "dbt_financialhome/tests/assert_no_unmapped_expense_categories.sql",
                "dbt_financialhome/tests/assert_monthly_spend_reconciles.sql",
                "dbt_financialhome/tests/assert_monthly_spend_grain.sql",
            ],
        ),
        PlanStep(
            step_id="STEP-05",
            name="Run build and evaluations",
            purpose="Execute dbt and independently verify the approved business examples.",
            commands=[
                "dbt seed --full-refresh",
                "dbt build",
                "agent-manager evaluate",
            ],
        ),
        PlanStep(
            step_id="STEP-06",
            name="Prepare evidence for human review",
            purpose="Report changed scope, assumptions, command output, evaluation results, and residual risk.",
            expected_files=["outputs/agent_run_report.md", "outputs/agent_run_report.json"],
            requires_human_approval=True,
        ),
    ]

    return RunPlan(
        change_id=change_id,
        objective=title,
        assumptions=assumptions,
        unresolved_questions=unresolved_questions,
        steps=steps,
    )
