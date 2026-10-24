"""Pattern 1: evaluate ticket triage against the human `tipo_caso` label."""

from __future__ import annotations

import csv
import json
import random
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass, field
from pathlib import Path
from statistics import median

from frasohome_decision.client import Decision, DecisionAPIError, DecisionClient
from frasohome_decision.policy import (
    DEFAULT_TRIAGE_POLICY,
    HUMAN_REVIEW,
    TriagePolicy,
    route,
)
from frasohome_decision.questions import triage_questions, triage_state

PRICE_PER_MILLION_INPUT_TOKENS = 0.042  # USD; output tokens are free


def sample_tickets(tickets: list[dict[str, str]], limit: int | None, seed: int = 42) -> list:
    rows = list(tickets)
    random.Random(seed).shuffle(rows)
    return rows[:limit] if limit else rows


@dataclass
class TriageReport:
    tickets: int
    accuracy: float
    median_latency_ms: float
    p95_latency_ms: float
    input_tokens: int
    cost_usd: float
    human_review: int
    priority: int
    errors: int = 0
    confusion: dict[str, dict[str, int]] = field(default_factory=dict)


def run_triage(
    client: DecisionClient,
    tickets: list[dict[str, str]],
    policy: TriagePolicy = DEFAULT_TRIAGE_POLICY,
    workers: int = 8,
) -> tuple[TriageReport, list[dict[str, object]]]:
    questions = triage_questions()

    def one(ticket: dict[str, str]) -> tuple[dict[str, str], Decision | None, str]:
        try:  # one failed ticket (after retries) is recorded, not fatal for the batch
            return ticket, client.decide(triage_state(ticket), questions), ""
        except DecisionAPIError as exc:
            return ticket, None, str(exc)

    with ThreadPoolExecutor(max_workers=max(1, workers)) as pool:
        results = list(pool.map(one, tickets))

    rows: list[dict[str, object]] = []
    confusion: dict[str, Counter] = defaultdict(Counter)
    latencies, tokens, correct, queues, errors = [], 0, 0, Counter(), 0
    for ticket, decision, error in results:
        if decision is None:
            errors += 1
            rows.append(
                {
                    "service_ticket_id": ticket["service_ticket_id"],
                    "canal": ticket["canal_soporte"],
                    "tipo_caso_label": ticket["tipo_caso"],
                    "queue": "error",
                    "prioridad_label": ticket["prioridad"],
                    "texto_cliente": ticket["texto_cliente"],
                    "error": error,
                }
            )
            continue
        predicted = decision.choice("case_type")
        queue = route(decision, policy)
        correct += predicted == ticket["tipo_caso"]
        confusion[ticket["tipo_caso"]][predicted] += 1
        latencies.append(decision.latency_ms)
        tokens += decision.input_tokens
        queues["human_review" if queue == HUMAN_REVIEW else queue.split(":")[-1]] += 1
        top = decision.top_probability("case_type")
        rows.append(
            {
                "service_ticket_id": ticket["service_ticket_id"],
                "canal": ticket["canal_soporte"],
                "tipo_caso_label": ticket["tipo_caso"],
                "case_type_pred": predicted,
                "case_type_top_p": round(top, 3) if top is not None else "",
                "frustration": round(decision.score("frustration"), 3),
                "is_blocked": round(decision.noul("is_blocked"), 3),
                "prioridad_label": ticket["prioridad"],
                "queue": queue,
                "latency_ms": round(decision.latency_ms, 1),
                "texto_cliente": ticket["texto_cliente"],
                "error": "",
            }
        )

    n = len(results) - errors  # tickets with a decision
    ordered = sorted(latencies)
    report = TriageReport(
        tickets=n,
        accuracy=correct / n if n else 0.0,
        median_latency_ms=median(ordered) if ordered else 0.0,
        p95_latency_ms=ordered[min(len(ordered) - 1, int(0.95 * len(ordered)))] if ordered else 0.0,
        input_tokens=tokens,
        cost_usd=tokens / 1_000_000 * PRICE_PER_MILLION_INPUT_TOKENS,
        human_review=queues["human_review"],
        priority=queues["priority"],
        errors=errors,
        confusion={label: dict(preds.most_common()) for label, preds in sorted(confusion.items())},
    )
    return report, rows


def write_outputs(report: TriageReport, rows: list[dict[str, object]], out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    if rows:
        with (out_dir / "triage_decisions.csv").open("w", newline="", encoding="utf-8") as f:
            fields = list(dict.fromkeys(k for row in rows for k in row))  # error rows are sparse
            writer = csv.DictWriter(f, fieldnames=fields)
            writer.writeheader()
            writer.writerows(rows)
    (out_dir / "triage_report.json").write_text(
        json.dumps(asdict(report), indent=2, ensure_ascii=False), encoding="utf-8"
    )


def format_report(report: TriageReport, policy: TriagePolicy) -> str:
    lines = [
        f"Tickets               : {report.tickets}",
        f"Accuracy vs tipo_caso : {report.accuracy:.1%}",
        f"Latency p50 / p95     : {report.median_latency_ms:.0f} / {report.p95_latency_ms:.0f} ms"
        " (client-side, includes network)",
        f"Input tokens          : {report.input_tokens:,}  ->  ${report.cost_usd:.6f}",
        f"Human review          : {report.human_review} (top p < {policy.min_confidence})",
        f"Priority queue        : {report.priority}",
        f"Errors                : {report.errors} (after retries; see the error column)",
        "",
        "Confusion (label -> predictions):",
    ]
    for label, preds in report.confusion.items():
        lines.append(f"  {label:14s} {preds}")
    return "\n".join(lines)
