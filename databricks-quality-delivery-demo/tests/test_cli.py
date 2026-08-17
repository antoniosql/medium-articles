from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_cli_run_and_gate() -> None:
    output_dir = ROOT / "artifacts_test"
    if output_dir.exists():
        for file in output_dir.iterdir():
            file.unlink()
        output_dir.rmdir()

    run_cmd = [
        sys.executable,
        "-m",
        "local_demo.cli",
        "run",
        "--data",
        str(ROOT / "data/customers.csv"),
        "--rules",
        str(ROOT / "rules/quality_rules.yml"),
        "--tag",
        "silver_hygiene",
        "--mode",
        "drop",
        "--output-dir",
        str(output_dir),
    ]
    run_result = subprocess.run(run_cmd, capture_output=True, text=True, check=False)
    assert run_result.returncode == 0, run_result.stderr

    gate_cmd = [
        sys.executable,
        "-m",
        "local_demo.cli",
        "gate",
        "--baseline",
        str(ROOT / "data/baseline_metrics.json"),
        "--actual",
        str(output_dir / "latest_metrics.json"),
    ]
    gate_result = subprocess.run(gate_cmd, capture_output=True, text=True, check=False)
    assert gate_result.returncode == 0, gate_result.stderr
