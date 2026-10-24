import csv
import json

from frasohome_decision.cli import main

NO_ENV = ["--env-file", "does-not-exist.env"]


def test_audit_labels(capsys):
    assert main([*NO_ENV, "audit-labels"]) == 0
    out = capsys.readouterr().out
    assert "conflicting prioridad" in out and "27 of 43" in out


def test_dry_runs_need_no_credentials(capsys):
    assert main([*NO_ENV, "triage", "--dry-run", "--limit", "5"]) == 0
    body = json.loads(capsys.readouterr().out)
    assert set(body["questions"]) == {"case_type", "frustration", "is_blocked"}

    assert main([*NO_ENV, "guardrails", "--dry-run"]) == 0
    body = json.loads(capsys.readouterr().out)
    assert len(body["questions"]) == 11

    assert main([*NO_ENV, "send", "examples/04-combined.json", "--dry-run"]) == 0


def test_send_example(fake_api, capsys, tmp_path):
    code = main([*NO_ENV, "send", "examples/02-choice.json", "--save", "--out-dir", str(tmp_path)])
    assert code == 0
    response = json.loads(capsys.readouterr().out)
    assert response["answers"]["team"]["choice"] in {"billing", "engineering", "support"}
    assert (tmp_path / "02-choice.response.json").exists()


def test_triage_end_to_end(fake_api, capsys, tmp_path):
    code = main([*NO_ENV, "triage", "--limit", "25", "--workers", "4", "--out-dir", str(tmp_path)])
    assert code == 0
    out = capsys.readouterr().out
    assert "Accuracy vs tipo_caso" in out
    assert len(fake_api.calls) == 25

    with (tmp_path / "triage_decisions.csv").open(encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 25
    assert {"case_type_pred", "queue", "prioridad_label"} <= set(rows[0])

    report = json.loads((tmp_path / "triage_report.json").read_text("utf-8"))
    assert report["tickets"] == 25
    assert 0 <= report["accuracy"] <= 1
    assert report["cost_usd"] > 0


def test_guardrails_blocks_the_sample_draft(fake_api, capsys):
    assert main([*NO_ENV, "guardrails"]) == 0
    assert "Verdict: BLOCK" in capsys.readouterr().out
    assert main([*NO_ENV, "guardrails", "--fail-on-block"]) == 2


def test_api_errors_exit_cleanly(fake_api, capsys):
    fake_api.fail_next = [403]
    assert main([*NO_ENV, "send", "examples/01-noul.json"]) == 1
    assert "HTTP 403" in capsys.readouterr().err


def test_triage_records_failed_tickets_and_keeps_going(fake_api, tmp_path):
    from frasohome_decision.client import DecisionClient
    from frasohome_decision.config import Settings
    from frasohome_decision.data import load_tickets
    from frasohome_decision.triage import run_triage, write_outputs

    fake_api.fail_next = [400]  # not retryable: the first ticket fails, the rest succeed
    client = DecisionClient(Settings.from_env(), timeout=5, retries=0)
    report, rows = run_triage(client, load_tickets()[:4], workers=1)
    assert report.errors == 1
    assert report.tickets == 3
    assert [r["queue"] for r in rows].count("error") == 1
    write_outputs(report, rows, tmp_path)
    assert "error" in (tmp_path / "triage_decisions.csv").read_text("utf-8").splitlines()[0]
