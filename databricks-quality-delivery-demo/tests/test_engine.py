from __future__ import annotations

import json
from pathlib import Path

from local_demo.engine import QualityEngine, evaluate_promotion_gate


ROOT = Path(__file__).resolve().parents[1]


def test_run_drop_mode_produces_expected_metrics(tmp_path: Path) -> None:
    engine = QualityEngine(ROOT / "rules/quality_rules.yml")
    metrics = engine.run(
        data_path=ROOT / "data/customers.csv",
        tag="silver_hygiene",
        mode="drop",
        output_dir=tmp_path,
    )

    assert metrics["input_rows"] == 8
    assert metrics["output_rows"] == 5
    assert metrics["dropped_rows"] == 3
    assert metrics["expectations"]["customer_id_not_null"]["failed_records"] == 1
    assert metrics["expectations"]["email_has_at"]["failed_records"] == 1
    assert metrics["expectations"]["country_allowed"]["failed_records"] == 1
    assert (tmp_path / "latest_metrics.json").exists()


def test_gate_passes_with_current_baseline(tmp_path: Path) -> None:
    engine = QualityEngine(ROOT / "rules/quality_rules.yml")
    engine.run(
        data_path=ROOT / "data/customers.csv",
        tag="silver_hygiene",
        mode="drop",
        output_dir=tmp_path,
    )

    result = evaluate_promotion_gate(
        ROOT / "data/baseline_metrics.json",
        tmp_path / "latest_metrics.json",
    )

    assert result["passed"] is True
    assert result["failures"] == []


def test_gate_fails_when_threshold_is_tighter(tmp_path: Path) -> None:
    engine = QualityEngine(ROOT / "rules/quality_rules.yml")
    engine.run(
        data_path=ROOT / "data/customers.csv",
        tag="silver_hygiene",
        mode="drop",
        output_dir=tmp_path,
    )

    strict_baseline = {
        "max_dropped_rows": 2,
        "max_failed_records_per_expectation": {
            "customer_id_not_null": 0,
            "email_has_at": 1,
            "country_allowed": 1,
        },
    }
    strict_path = tmp_path / "strict_baseline.json"
    strict_path.write_text(json.dumps(strict_baseline), encoding="utf-8")

    result = evaluate_promotion_gate(strict_path, tmp_path / "latest_metrics.json")

    assert result["passed"] is False
    assert len(result["failures"]) >= 1
