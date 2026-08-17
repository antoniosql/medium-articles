from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .engine import QualityEngine, QualityEngineError, evaluate_promotion_gate


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Quality delivery demo CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("run", help="Run the local quality pipeline")
    run_parser.add_argument("--data", required=True, help="Path to input CSV data")
    run_parser.add_argument("--rules", required=True, help="Path to rules YAML")
    run_parser.add_argument("--tag", required=True, help="Rule tag to apply")
    run_parser.add_argument(
        "--mode",
        default="drop",
        choices=["drop", "fail"],
        help="How to handle invalid rows",
    )
    run_parser.add_argument(
        "--output-dir",
        default="artifacts",
        help="Directory where outputs will be written",
    )

    gate_parser = subparsers.add_parser("gate", help="Evaluate promotion gate")
    gate_parser.add_argument("--baseline", required=True, help="Baseline JSON file")
    gate_parser.add_argument("--actual", required=True, help="Actual metrics JSON file")

    return parser


def cmd_run(args: argparse.Namespace) -> int:
    engine = QualityEngine(args.rules)
    try:
        metrics = engine.run(
            data_path=args.data,
            tag=args.tag,
            mode=args.mode,
            output_dir=args.output_dir,
        )
    except QualityEngineError as exc:
        print(f"Run failed: {exc}", file=sys.stderr)
        return 1

    print(json.dumps(metrics, indent=2))
    return 0


def cmd_gate(args: argparse.Namespace) -> int:
    result = evaluate_promotion_gate(args.baseline, args.actual)
    print(json.dumps(result, indent=2))
    return 0 if result["passed"] else 1


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "run":
        return cmd_run(args)
    if args.command == "gate":
        return cmd_gate(args)

    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
