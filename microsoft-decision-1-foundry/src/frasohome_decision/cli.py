"""decision-demo: run the article's examples against a Microsoft-Decision-1 deployment.

Commands
  send <file.json>   Send one example request from ./examples and print the raw response
  triage             Pattern 1: route FraSoHome tickets, measure accuracy, latency and cost
  guardrails         Pattern 2: check a GenAI email draft against the brand rules
  audit-labels       Offline: label consistency of the ticket extract (article numbers)

Online commands read AZURE_ENDPOINT, DEPLOYMENT_NAME and optional AZURE_API_KEY from
the environment or from .env. Use --dry-run to print requests without calling the API.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from frasohome_decision.audit import audit_labels
from frasohome_decision.client import DecisionAPIError, DecisionClient
from frasohome_decision.config import Settings, load_env_file
from frasohome_decision.data import (
    DRAFT_JSON,
    RULES_CSV,
    TICKETS_CSV,
    load_draft,
    load_rules,
    load_tickets,
)
from frasohome_decision.policy import GatePolicy, TriagePolicy, gate
from frasohome_decision.questions import guardrail_questions, triage_questions, triage_state
from frasohome_decision.triage import format_report, run_triage, sample_tickets, write_outputs

DEPLOYMENT_PLACEHOLDER = "<deployment-name>"


def _client(args: argparse.Namespace) -> DecisionClient:
    return DecisionClient(Settings.from_env(), timeout=args.timeout)


def _print_json(data: object) -> None:
    print(json.dumps(data, indent=2, ensure_ascii=False))


def cmd_send(args: argparse.Namespace) -> int:
    body = json.loads(Path(args.file).read_text(encoding="utf-8"))
    if args.dry_run:
        _print_json(body)
        return 0
    decision = _client(args).post(body)
    _print_json(decision.raw)
    print(f"\n{decision.latency_ms:.0f} ms, {decision.input_tokens} input tokens", file=sys.stderr)
    if args.save:
        out = Path(args.out_dir) / f"{Path(args.file).stem}.response.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(decision.raw, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"Saved {out}", file=sys.stderr)
    return 0


def cmd_triage(args: argparse.Namespace) -> int:
    tickets = sample_tickets(load_tickets(Path(args.csv)), args.limit, seed=args.seed)
    policy = TriagePolicy(min_confidence=args.min_confidence)
    if args.dry_run:
        _print_json(
            {
                "model": DEPLOYMENT_PLACEHOLDER,
                "state": triage_state(tickets[0]),
                "questions": triage_questions(),
            }
        )
        print(f"\n{len(tickets)} tickets would be sent, one request each.", file=sys.stderr)
        return 0
    report, rows = run_triage(_client(args), tickets, policy, workers=args.workers)
    print(format_report(report, policy))
    write_outputs(report, rows, Path(args.out_dir))
    print(f"\nPer-ticket decisions: {Path(args.out_dir) / 'triage_decisions.csv'}")
    return 0


def cmd_guardrails(args: argparse.Namespace) -> int:
    rules = load_rules(Path(args.csv))
    draft = load_draft(Path(args.draft))
    questions = guardrail_questions(rules, draft["canal"])
    if args.dry_run:
        _print_json({"model": DEPLOYMENT_PLACEHOLDER, "state": draft, "questions": questions})
        print(f"\n{len(questions)} rule checks in a single request.", file=sys.stderr)
        return 0
    decision = _client(args).decide(draft, questions)
    severities = {r["regla_id"]: r["severidad"] for r in rules}
    result = gate(decision, severities, GatePolicy())
    for rule_id, p in result.probabilities.items():
        print(f"  {rule_id} ({severities.get(rule_id, '?'):5s}) p_violation={p:.3f}")
    print(f"\nVerdict: {result.verdict}")
    print(f"  block : {result.blocked_by}")
    print(f"  review: {result.review_for}")
    print(
        f"{len(questions)} checks in one call, {decision.latency_ms:.0f} ms, "
        f"{decision.input_tokens} input tokens"
    )
    return 0 if result.verdict == "SEND" or not args.fail_on_block else 2


def cmd_audit(args: argparse.Namespace) -> int:
    audit = audit_labels(load_tickets(Path(args.csv)))
    n = audit.repeated_texts
    print(f"Tickets                   : {audit.tickets}")
    print(f"Messages repeated verbatim: {n} ({audit.rows_in_repeated_texts} tickets)")
    for column, count in audit.conflicting.items():
        print(f"  conflicting {column:20s}: {count} of {n}")
    text, priorities = audit.worst_example
    print(f"\nWorst case ({sum(priorities.values())} copies): {text}")
    print(f"  prioridad labels: {dict(priorities)}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="decision-demo", description=__doc__, formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument("--env-file", default=".env", help="dotenv file to load (default: .env)")
    parser.add_argument("--timeout", type=float, default=30.0, help="HTTP timeout in seconds")
    sub = parser.add_subparsers(dest="command", required=True)

    send = sub.add_parser("send", help="send one example request from ./examples")
    send.add_argument("file")
    send.add_argument("--dry-run", action="store_true")
    send.add_argument("--save", action="store_true", help="save the response under --out-dir")
    send.add_argument("--out-dir", default="outputs")
    send.set_defaults(func=cmd_send)

    triage = sub.add_parser("triage", help="Pattern 1: ticket triage evaluation")
    triage.add_argument("--csv", default=str(TICKETS_CSV))
    triage.add_argument("--limit", type=int, default=100, help="0 = all tickets")
    triage.add_argument("--seed", type=int, default=42)
    triage.add_argument("--workers", type=int, default=8)
    triage.add_argument("--min-confidence", type=float, default=0.6)
    triage.add_argument("--out-dir", default="outputs")
    triage.add_argument("--dry-run", action="store_true")
    triage.set_defaults(func=cmd_triage)

    guard = sub.add_parser("guardrails", help="Pattern 2: brand gate for a GenAI draft")
    guard.add_argument("--csv", default=str(RULES_CSV))
    guard.add_argument("--draft", default=str(DRAFT_JSON))
    guard.add_argument("--dry-run", action="store_true")
    guard.add_argument("--fail-on-block", action="store_true", help="exit 2 unless verdict is SEND")
    guard.set_defaults(func=cmd_guardrails)

    audit = sub.add_parser("audit-labels", help="offline: label consistency of the tickets")
    audit.add_argument("--csv", default=str(TICKETS_CSV))
    audit.set_defaults(func=cmd_audit)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    load_env_file(Path(args.env_file))
    try:
        return args.func(args)
    except DecisionAPIError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
