from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from .models import ValidationIssue


CONTRACT_FILES = {
    "intent": "intent_contract.yml",
    "decision_rights": "decision_rights.yml",
    "quality_gates": "quality_gates.yml",
    "evaluation_cases": "evaluation_cases.yml",
}


def load_yaml(path: Path) -> dict[str, Any]:
    try:
        content = yaml.safe_load(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError(f"Required contract not found: {path}") from exc
    except yaml.YAMLError as exc:
        raise ValueError(f"Invalid YAML in {path}: {exc}") from exc

    if not isinstance(content, dict):
        raise ValueError(f"Contract must contain a YAML mapping: {path}")
    return content


def load_contracts(contracts_dir: Path) -> dict[str, dict[str, Any]]:
    return {
        name: load_yaml(contracts_dir / filename)
        for name, filename in CONTRACT_FILES.items()
    }


def validate_contracts(contracts: dict[str, dict[str, Any]]) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []

    required_top_level = {
        "intent": [
            "version",
            "change_id",
            "title",
            "owner",
            "business_question",
            "source_scope",
            "business_rules",
            "deliverables",
            "acceptance_criteria",
        ],
        "decision_rights": [
            "version",
            "agent_role",
            "autonomous_actions",
            "human_approval_required",
            "prohibited_actions",
            "stop_conditions",
        ],
        "quality_gates": ["version", "gates", "warning_policy"],
        "evaluation_cases": ["version", "output_model", "cases"],
    }

    for contract_name, keys in required_top_level.items():
        payload = contracts.get(contract_name)
        if payload is None:
            issues.append(
                ValidationIssue("error", contract_name, "Contract was not loaded")
            )
            continue
        for key in keys:
            if key not in payload or payload[key] in (None, "", []):
                issues.append(
                    ValidationIssue(
                        "error",
                        f"{contract_name}.{key}",
                        "Required value is missing or empty",
                    )
                )

    intent = contracts.get("intent", {})
    evaluations = contracts.get("evaluation_cases", {})
    required_measures = {
        item.get("name")
        for item in intent.get("required_measures", [])
        if isinstance(item, dict)
    }
    expected_measures = {
        "actual_spend_eur",
        "budget_eur",
        "variance_eur",
        "variance_pct",
    }
    missing_measures = expected_measures - required_measures
    for measure in sorted(missing_measures):
        issues.append(
            ValidationIssue(
                "error",
                "intent.required_measures",
                f"Required demo measure is missing: {measure}",
            )
        )

    output_model = evaluations.get("output_model")
    intended_model = intent.get("required_grain", {}).get("model")
    if output_model and intended_model and output_model != intended_model:
        issues.append(
            ValidationIssue(
                "error",
                "evaluation_cases.output_model",
                f"Evaluation output model '{output_model}' does not match intent '{intended_model}'",
            )
        )

    case_ids: set[str] = set()
    for index, case in enumerate(evaluations.get("cases", [])):
        location = f"evaluation_cases.cases[{index}]"
        if not isinstance(case, dict):
            issues.append(ValidationIssue("error", location, "Case must be a mapping"))
            continue
        for key in ("id", "name", "query", "expected", "tolerance"):
            if key not in case:
                issues.append(
                    ValidationIssue("error", f"{location}.{key}", "Required value is missing")
                )
        case_id = str(case.get("id", ""))
        if case_id in case_ids:
            issues.append(
                ValidationIssue("error", f"{location}.id", f"Duplicate case id: {case_id}")
            )
        case_ids.add(case_id)

    gate_ids: set[str] = set()
    for index, gate in enumerate(contracts.get("quality_gates", {}).get("gates", [])):
        location = f"quality_gates.gates[{index}]"
        if not isinstance(gate, dict):
            issues.append(ValidationIssue("error", location, "Gate must be a mapping"))
            continue
        gate_id = str(gate.get("id", ""))
        if not gate_id:
            issues.append(ValidationIssue("error", f"{location}.id", "Gate id is required"))
        elif gate_id in gate_ids:
            issues.append(
                ValidationIssue("error", f"{location}.id", f"Duplicate gate id: {gate_id}")
            )
        gate_ids.add(gate_id)
        if gate.get("blocking") is not True:
            issues.append(
                ValidationIssue(
                    "warning",
                    f"{location}.blocking",
                    "Reference demo expects every listed gate to be blocking",
                )
            )

    return issues


def has_errors(issues: list[ValidationIssue]) -> bool:
    return any(issue.severity == "error" for issue in issues)
