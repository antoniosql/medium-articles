from __future__ import annotations

import os
import shutil
import subprocess
import time
from pathlib import Path

from .models import CommandResult


def command_available(command: str) -> bool:
    return shutil.which(command) is not None


def run_command(
    command: list[str],
    cwd: Path,
    extra_env: dict[str, str] | None = None,
) -> CommandResult:
    env = os.environ.copy()
    if extra_env:
        env.update(extra_env)

    started = time.perf_counter()
    completed = subprocess.run(
        command,
        cwd=cwd,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )
    duration = time.perf_counter() - started

    return CommandResult(
        command=command,
        return_code=completed.returncode,
        stdout=completed.stdout,
        stderr=completed.stderr,
        duration_seconds=duration,
    )


def run_dbt_build(
    repo_root: Path,
    scenario: str,
) -> list[CommandResult]:
    project_dir = repo_root / "dbt_financialhome"
    profiles_dir = repo_root / "profiles"
    data_dir = repo_root / ".data"
    data_dir.mkdir(parents=True, exist_ok=True)

    database_path = data_dir / f"financialhome_{scenario}.duckdb"
    if database_path.exists():
        database_path.unlink()

    env = {
        "DUCKDB_PATH": str(database_path.resolve()),
        "DBT_PROFILES_DIR": str(profiles_dir.resolve()),
    }

    scenario_vars = json_vars(scenario)
    commands = [
        ["dbt", "seed", "--full-refresh", "--vars", scenario_vars],
        ["dbt", "build", "--vars", scenario_vars],
    ]

    results: list[CommandResult] = []
    for command in commands:
        result = run_command(command, cwd=project_dir, extra_env=env)
        results.append(result)
        if not result.passed:
            break
    return results


def json_vars(scenario: str) -> str:
    safe_scenario = scenario if scenario in {"normal", "unmapped_category"} else "normal"
    return '{"failure_scenario": "' + safe_scenario + '"}'
