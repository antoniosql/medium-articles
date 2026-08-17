from __future__ import annotations

from pathlib import Path
from typing import Any

from .models import EvaluationResult


def evaluate_cases(
    database_path: Path,
    evaluation_contract: dict[str, Any],
) -> list[EvaluationResult]:
    try:
        import duckdb
    except ImportError as exc:
        raise RuntimeError(
            "DuckDB is not installed. Install the project dependencies before evaluation."
        ) from exc

    results: list[EvaluationResult] = []
    connection = duckdb.connect(str(database_path), read_only=True)
    try:
        for case in evaluation_contract.get("cases", []):
            case_id = str(case["id"])
            name = str(case["name"])
            expected = float(case["expected"])
            tolerance = float(case["tolerance"])
            try:
                row = connection.execute(str(case["query"])).fetchone()
                actual = None if row is None or row[0] is None else float(row[0])
                passed = actual is not None and abs(actual - expected) <= tolerance
                results.append(
                    EvaluationResult(
                        case_id=case_id,
                        name=name,
                        expected=expected,
                        actual=actual,
                        tolerance=tolerance,
                        passed=passed,
                    )
                )
            except Exception as exc:  # db engine errors are evidence, not crashes
                results.append(
                    EvaluationResult(
                        case_id=case_id,
                        name=name,
                        expected=expected,
                        actual=None,
                        tolerance=tolerance,
                        passed=False,
                        error=str(exc),
                    )
                )
    finally:
        connection.close()

    return results
