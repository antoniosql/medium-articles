from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from .models import RunPlan


PLAN_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": [
        "change_id",
        "objective",
        "assumptions",
        "unresolved_questions",
        "steps",
    ],
    "properties": {
        "change_id": {"type": "string"},
        "objective": {"type": "string"},
        "assumptions": {"type": "array", "items": {"type": "string"}},
        "unresolved_questions": {"type": "array", "items": {"type": "string"}},
        "steps": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": [
                    "step_id",
                    "name",
                    "purpose",
                    "expected_files",
                    "commands",
                    "requires_human_approval",
                ],
                "properties": {
                    "step_id": {"type": "string"},
                    "name": {"type": "string"},
                    "purpose": {"type": "string"},
                    "expected_files": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                    "commands": {"type": "array", "items": {"type": "string"}},
                    "requires_human_approval": {"type": "boolean"},
                },
            },
        },
    },
}


def create_openai_plan(repo_root: Path, contracts: dict[str, dict[str, Any]]) -> RunPlan:
    try:
        from openai import OpenAI
    except ImportError as exc:
        raise RuntimeError(
            "The OpenAI planner requires the optional dependency: pip install -e '.[llm]'"
        ) from exc

    model = os.getenv("OPENAI_MODEL")
    if not model:
        raise RuntimeError("OPENAI_MODEL must be set for the optional OpenAI planner")

    agent_instructions = (repo_root / "AGENTS.md").read_text(encoding="utf-8")
    context = {
        "agent_instructions": agent_instructions,
        "contracts": contracts,
    }

    developer_message = """
You are planning a governed analytics-engineering change. Return only a plan that
conforms to the supplied JSON schema. Respect the decision rights. Do not grant
yourself merge, deployment, production access, or authority to redefine metrics.
The plan must include executable validation and an explicit final human-review step.
""".strip()

    client = OpenAI()
    response = client.responses.create(
        model=model,
        input=[
            {"role": "developer", "content": developer_message},
            {
                "role": "user",
                "content": "Create the change plan from this context:\n" + json.dumps(context),
            },
        ],
        text={
            "format": {
                "type": "json_schema",
                "name": "analytics_change_plan",
                "strict": True,
                "schema": PLAN_SCHEMA,
            }
        },
    )

    if not response.output_text:
        raise RuntimeError("The model returned no plan text")

    try:
        payload = json.loads(response.output_text)
    except json.JSONDecodeError as exc:
        raise RuntimeError("The model did not return valid JSON") from exc

    return RunPlan.from_dict(payload)
