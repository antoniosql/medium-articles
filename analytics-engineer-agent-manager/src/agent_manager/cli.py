from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .contracts import has_errors, load_contracts, validate_contracts
from .evaluator import evaluate_cases
from .executor import command_available, run_dbt_build
from .models import AgentRun
from .planner import create_deterministic_plan
from .reporter import render_plan, write_plan, write_run_report


def repo_root() -> Path:
    candidates = [Path.cwd(), Path(__file__).resolve().parents[2]]
    for candidate in candidates:
        if (candidate / "contracts").is_dir() and (candidate / "dbt_financialhome").is_dir():
            return candidate.resolve()
    return Path(__file__).resolve().parents[2]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="agent-manager",
        description="Governed analytics-engineering agent workflow",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("validate", help="Validate context contracts")

    plan_parser = subparsers.add_parser("plan", help="Generate an agent plan")
    plan_parser.add_argument(
        "--planner",
        choices=["deterministic", "openai"],
        default="deterministic",
    )
    plan_parser.add_argument(
        "--output",
        default="outputs/agent_plan.md",
        help="Plan output path relative to the repository root",
    )

    evaluate_parser = subparsers.add_parser(
        "evaluate", help="Run business evaluation cases against a built DuckDB database"
    )
    evaluate_parser.add_argument(
        "--scenario",
        choices=["normal", "unmapped_category"],
        default="normal",
    )

    demo_parser = subparsers.add_parser("demo", help="Run the complete governed demo")
    demo_parser.add_argument(
        "--scenario",
        choices=["normal", "unmapped_category"],
        default="normal",
    )
    demo_parser.add_argument(
        "--planner",
        choices=["deterministic", "openai"],
        default="deterministic",
    )

    return parser


def load_and_validate(root: Path):
    contracts = load_contracts(root / "contracts")
    issues = validate_contracts(contracts)
    return contracts, issues


def create_plan(root: Path, contracts, planner_name: str):
    if planner_name == "openai":
        from .openai_planner import create_openai_plan

        return create_openai_plan(root, contracts)
    return create_deterministic_plan(contracts)


def print_issues(issues) -> None:
    if not issues:
        print("Context contracts are valid.")
        return
    for issue in issues:
        print(f"[{issue.severity.upper()}] {issue.location}: {issue.message}")


def command_validate(root: Path) -> int:
    _, issues = load_and_validate(root)
    print_issues(issues)
    return 1 if has_errors(issues) else 0


def command_plan(root: Path, planner_name: str, output: str) -> int:
    contracts, issues = load_and_validate(root)
    print_issues(issues)
    if has_errors(issues):
        return 1
    plan = create_plan(root, contracts, planner_name)
    output_path = root / output
    write_plan(plan, output_path)
    print(render_plan(plan))
    print(f"Plan written to {output_path}")
    return 0


def database_path(root: Path, scenario: str) -> Path:
    return root / ".data" / f"financialhome_{scenario}.duckdb"


def command_evaluate(root: Path, scenario: str) -> int:
    contracts, issues = load_and_validate(root)
    if has_errors(issues):
        print_issues(issues)
        return 1
    path = database_path(root, scenario)
    if not path.exists():
        print(f"Database not found: {path}. Run 'agent-manager demo' first.")
        return 1
    results = evaluate_cases(path, contracts["evaluation_cases"])
    for result in results:
        status = "PASS" if result.passed else "FAIL"
        print(
            f"[{status}] {result.case_id} {result.name}: "
            f"expected={result.expected} actual={result.actual} tolerance={result.tolerance}"
        )
    return 0 if all(result.passed for result in results) else 1


def command_demo(root: Path, scenario: str, planner_name: str) -> int:
    contracts, issues = load_and_validate(root)
    plan = create_plan(root, contracts, planner_name)
    run = AgentRun(
        change_id=plan.change_id,
        scenario=scenario,
        planner=planner_name,
        plan=plan,
        context_valid=not has_errors(issues),
        validation_issues=issues,
    )

    if has_errors(issues):
        run.blocking_reason = "Context validation failed. No build command was executed."
    elif not command_available("dbt"):
        run.blocking_reason = (
            "The dbt executable is not available. Install the project with "
            "'python -m pip install -e .[dev]' and rerun the demo."
        )
    else:
        run.commands = run_dbt_build(root, scenario)
        if not all(result.passed for result in run.commands):
            if scenario == "unmapped_category":
                run.blocking_reason = (
                    "Expected guardrail activation: dbt rejected an unmapped expense category."
                )
            else:
                run.blocking_reason = "A blocking dbt command failed."
        else:
            run.evaluations = evaluate_cases(
                database_path(root, scenario), contracts["evaluation_cases"]
            )
            if not all(result.passed for result in run.evaluations):
                run.blocking_reason = "One or more business evaluation cases failed."

    markdown_path, json_path = write_run_report(run, root / "outputs")
    print(f"Evidence report: {markdown_path}")
    print(f"JSON evidence: {json_path}")
    print(f"Final status: {'PASS' if run.passed else 'BLOCKED'}")

    expected_guardrail_triggered = (
        scenario == "unmapped_category"
        and any(not result.passed for result in run.commands)
        and run.blocking_reason is not None
        and run.blocking_reason.startswith("Expected guardrail activation")
    )
    if expected_guardrail_triggered:
        # The expected-failure scenario succeeds only when dbt itself activates the gate.
        return 0
    return 0 if run.passed else 1


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    root = repo_root()

    try:
        if args.command == "validate":
            code = command_validate(root)
        elif args.command == "plan":
            code = command_plan(root, args.planner, args.output)
        elif args.command == "evaluate":
            code = command_evaluate(root, args.scenario)
        elif args.command == "demo":
            code = command_demo(root, args.scenario, args.planner)
        else:  # pragma: no cover
            parser.error(f"Unknown command: {args.command}")
            return
    except (RuntimeError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        code = 1

    raise SystemExit(code)


if __name__ == "__main__":
    main()
