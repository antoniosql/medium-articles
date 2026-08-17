from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import json
from typing import Any

import pandas as pd
import yaml


@dataclass(frozen=True)
class Rule:
    name: str
    tag: str
    constraint: str
    description: str


class QualityEngineError(Exception):
    pass


class PromotionGateError(Exception):
    pass


class QualityEngine:
    def __init__(self, rules_path: str | Path) -> None:
        self.rules_path = Path(rules_path)
        self.rules = self._load_rules()

    def _load_rules(self) -> list[Rule]:
        payload = yaml.safe_load(self.rules_path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict) or "rules" not in payload:
            raise QualityEngineError("Rules file must contain a top-level 'rules' list.")

        rules: list[Rule] = []
        for item in payload["rules"]:
            rules.append(
                Rule(
                    name=item["name"],
                    tag=item["tag"],
                    constraint=item["constraint"],
                    description=item.get("description", item["name"]),
                )
            )
        return rules

    def get_rules(self, tag: str) -> list[Rule]:
        return [rule for rule in self.rules if rule.tag == tag]

    def _evaluate_constraint(self, df: pd.DataFrame, constraint: str) -> pd.Series:
        if ".not_null" in constraint:
            column = constraint.split(".not_null")[0]
            return df[column].notna()

        if ".contains:" in constraint:
            column, needle = constraint.split(".contains:", maxsplit=1)
            return df[column].fillna("").astype(str).str.contains(needle, regex=False)

        if ".in:" in constraint:
            column, allowed = constraint.split(".in:", maxsplit=1)
            values = [value.strip() for value in allowed.split(",") if value.strip()]
            return df[column].isin(values)

        raise QualityEngineError(f"Unsupported constraint syntax: {constraint}")

    def run(
        self,
        data_path: str | Path,
        tag: str,
        mode: str = "drop",
        output_dir: str | Path = "artifacts",
    ) -> dict[str, Any]:
        if mode not in {"drop", "fail"}:
            raise QualityEngineError("mode must be either 'drop' or 'fail'.")

        df = pd.read_csv(data_path)
        rules = self.get_rules(tag)
        if not rules:
            raise QualityEngineError(f"No rules found for tag '{tag}'.")

        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        metrics: dict[str, Any] = {
            "dataset": Path(data_path).stem,
            "mode": mode,
            "input_rows": int(len(df)),
            "output_rows": 0,
            "dropped_rows": 0,
            "expectations": {},
        }

        valid_mask = pd.Series([True] * len(df), index=df.index)

        for rule in rules:
            passed = self._evaluate_constraint(df, rule.constraint)
            failed = ~passed

            metrics["expectations"][rule.name] = {
                "passed_records": int(passed.sum()),
                "failed_records": int(failed.sum()),
                "description": rule.description,
            }

            if mode == "fail" and int(failed.sum()) > 0:
                raise QualityEngineError(
                    f"Expectation '{rule.name}' failed with {int(failed.sum())} invalid records."
                )

            valid_mask &= passed

        clean_df = df[valid_mask].copy()
        metrics["output_rows"] = int(len(clean_df))
        metrics["dropped_rows"] = int(len(df) - len(clean_df))

        clean_df.to_csv(output_path / f"clean_{Path(data_path).name}", index=False)
        (output_path / "latest_metrics.json").write_text(
            json.dumps(metrics, indent=2), encoding="utf-8"
        )

        return metrics


def evaluate_promotion_gate(baseline_path: str | Path, actual_path: str | Path) -> dict[str, Any]:
    baseline = json.loads(Path(baseline_path).read_text(encoding="utf-8"))
    actual = json.loads(Path(actual_path).read_text(encoding="utf-8"))

    failures: list[str] = []

    actual_dropped = int(actual.get("dropped_rows", 0))
    max_dropped = int(baseline.get("max_dropped_rows", 0))
    if actual_dropped > max_dropped:
        failures.append(
            f"Dropped rows {actual_dropped} exceed allowed maximum {max_dropped}."
        )

    baseline_rules = baseline.get("max_failed_records_per_expectation", {})
    actual_rules = actual.get("expectations", {})

    for rule_name, max_failed in baseline_rules.items():
        actual_failed = int(actual_rules.get(rule_name, {}).get("failed_records", 0))
        if actual_failed > int(max_failed):
            failures.append(
                f"Expectation '{rule_name}' has {actual_failed} failed records, above the threshold {max_failed}."
            )

    result = {
        "passed": len(failures) == 0,
        "failures": failures,
    }
    return result
