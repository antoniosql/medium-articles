# Agent run evidence — FH-001

**Status:** PASS
**Scenario:** `normal`
**Planner:** `deterministic`

> This example illustrates the report structure produced after a successful local run. It is evidence for human review, not authorization to merge or deploy.

## Context validation

Context valid: **True**

No validation issues.

## Command evidence

| Command | Result |
|---|---:|
| `dbt seed --full-refresh` | PASS |
| `dbt build` | PASS |

## Business evaluation evidence

| Case | Expected | Actual | Result |
|---|---:|---:|---:|
| EVAL-001 January total spend excludes income | 1925.00 | 1925.00 | PASS |
| EVAL-002 February total spend is correct | 2292.00 | 2292.00 | PASS |
| EVAL-003 March insurance variance | 270.00 | 270.00 | PASS |
| EVAL-004 January telecommunications spend | 85.00 | 85.00 | PASS |
| EVAL-005 Full reconciliation difference | 0.00 | 0.00 | PASS |

## Required human review

- Confirm business semantics.
- Review unresolved questions.
- Confirm no gate was weakened.
- Approve or reject the change.

The agent must not merge or deploy.
