from __future__ import annotations

import json
from pathlib import Path

from .models import AgentRun, RunPlan


def render_plan(plan: RunPlan) -> str:
    lines = [
        f"# Agent plan — {plan.change_id}",
        "",
        f"**Objective:** {plan.objective}",
        "",
        "## Assumptions",
        "",
    ]
    lines.extend(f"- {item}" for item in plan.assumptions)
    lines.extend(["", "## Unresolved questions", ""])
    lines.extend(f"- {item}" for item in plan.unresolved_questions)
    lines.extend(["", "## Steps", ""])

    for step in plan.steps:
        approval = " — **human approval required**" if step.requires_human_approval else ""
        lines.extend(
            [
                f"### {step.step_id}: {step.name}{approval}",
                "",
                step.purpose,
                "",
            ]
        )
        if step.expected_files:
            lines.append("Expected files:")
            lines.extend(f"- `{item}`" for item in step.expected_files)
            lines.append("")
        if step.commands:
            lines.append("Commands:")
            lines.extend(f"- `{item}`" for item in step.commands)
            lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def render_run_report(run: AgentRun) -> str:
    status = "PASS" if run.passed else "BLOCKED"
    lines = [
        f"# Agent run evidence — {run.change_id}",
        "",
        f"**Status:** {status}",
        f"**Scenario:** `{run.scenario}`",
        f"**Planner:** `{run.planner}`",
        "",
        "> This report is evidence for human review. It is not authorization to merge or deploy.",
        "",
        "## Context validation",
        "",
        f"Context valid: **{run.context_valid}**",
        "",
    ]

    if run.validation_issues:
        lines.append("| Severity | Location | Message |")
        lines.append("|---|---|---|")
        for issue in run.validation_issues:
            lines.append(f"| {issue.severity} | `{issue.location}` | {issue.message} |")
    else:
        lines.append("No validation issues.")

    lines.extend(["", "## Plan", "", f"Objective: {run.plan.objective}", ""])
    for step in run.plan.steps:
        gate = " (approval gated)" if step.requires_human_approval else ""
        lines.append(f"- **{step.step_id} — {step.name}**{gate}: {step.purpose}")

    lines.extend(["", "## Command evidence", ""])
    if run.commands:
        lines.append("| Command | Result | Duration |")
        lines.append("|---|---:|---:|")
        for result in run.commands:
            command = " ".join(result.command)
            command_status = "PASS" if result.passed else "FAIL"
            lines.append(
                f"| `{command}` | {command_status} | {result.duration_seconds:.2f}s |"
            )
            if not result.passed:
                excerpt = (result.stderr or result.stdout).strip()[-1500:]
                lines.extend(["", "```text", excerpt, "```", ""])
    else:
        lines.append("No commands were executed.")

    lines.extend(["", "## Business evaluation evidence", ""])
    if run.evaluations:
        lines.append("| Case | Expected | Actual | Tolerance | Result |")
        lines.append("|---|---:|---:|---:|---:|")
        for item in run.evaluations:
            actual = "n/a" if item.actual is None else f"{item.actual:.2f}"
            result = "PASS" if item.passed else "FAIL"
            lines.append(
                f"| {item.case_id}: {item.name} | {item.expected:.2f} | {actual} | "
                f"{item.tolerance:.2f} | {result} |"
            )
            if item.error:
                lines.append(f"\nError for `{item.case_id}`: `{item.error}`\n")
    else:
        lines.append("No business evaluations were executed.")

    lines.extend(["", "## Blocking reason", ""])
    lines.append(run.blocking_reason or "None.")

    lines.extend(
        [
            "",
            "## Required human review",
            "",
            "- Confirm that monthly grain and metric definitions match the business intent.",
            "- Review unresolved questions and decide whether they belong in a later change.",
            "- Confirm that no quality gate was bypassed or weakened.",
            "- Approve or reject the change. The agent must not merge or deploy it.",
            "",
        ]
    )
    return "\n".join(lines)


def write_plan(plan: RunPlan, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(render_plan(plan), encoding="utf-8")


def write_run_report(run: AgentRun, output_dir: Path) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    markdown_path = output_dir / "agent_run_report.md"
    json_path = output_dir / "agent_run_report.json"
    markdown_path.write_text(render_run_report(run), encoding="utf-8")
    json_path.write_text(json.dumps(run.to_dict(), indent=2), encoding="utf-8")
    return markdown_path, json_path
