from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class PlanStep:
    step_id: str
    name: str
    purpose: str
    expected_files: list[str] = field(default_factory=list)
    commands: list[str] = field(default_factory=list)
    requires_human_approval: bool = False

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PlanStep":
        return cls(
            step_id=str(data["step_id"]),
            name=str(data["name"]),
            purpose=str(data["purpose"]),
            expected_files=[str(item) for item in data.get("expected_files", [])],
            commands=[str(item) for item in data.get("commands", [])],
            requires_human_approval=bool(data.get("requires_human_approval", False)),
        )


@dataclass(frozen=True)
class RunPlan:
    change_id: str
    objective: str
    assumptions: list[str]
    unresolved_questions: list[str]
    steps: list[PlanStep]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "RunPlan":
        return cls(
            change_id=str(data["change_id"]),
            objective=str(data["objective"]),
            assumptions=[str(item) for item in data.get("assumptions", [])],
            unresolved_questions=[str(item) for item in data.get("unresolved_questions", [])],
            steps=[PlanStep.from_dict(item) for item in data.get("steps", [])],
        )


@dataclass(frozen=True)
class ValidationIssue:
    severity: str
    location: str
    message: str


@dataclass(frozen=True)
class CommandResult:
    command: list[str]
    return_code: int
    stdout: str
    stderr: str
    duration_seconds: float

    @property
    def passed(self) -> bool:
        return self.return_code == 0


@dataclass(frozen=True)
class EvaluationResult:
    case_id: str
    name: str
    expected: float
    actual: float | None
    tolerance: float
    passed: bool
    error: str | None = None


@dataclass
class AgentRun:
    change_id: str
    scenario: str
    planner: str
    plan: RunPlan
    context_valid: bool
    validation_issues: list[ValidationIssue]
    commands: list[CommandResult] = field(default_factory=list)
    evaluations: list[EvaluationResult] = field(default_factory=list)
    blocking_reason: str | None = None

    @property
    def passed(self) -> bool:
        return (
            self.context_valid
            and self.blocking_reason is None
            and all(item.passed for item in self.commands)
            and all(item.passed for item in self.evaluations)
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "change_id": self.change_id,
            "scenario": self.scenario,
            "planner": self.planner,
            "passed": self.passed,
            "context_valid": self.context_valid,
            "blocking_reason": self.blocking_reason,
            "validation_issues": [asdict(item) for item in self.validation_issues],
            "plan": self.plan.to_dict(),
            "commands": [
                {
                    **asdict(item),
                    "passed": item.passed,
                }
                for item in self.commands
            ],
            "evaluations": [asdict(item) for item in self.evaluations],
        }
