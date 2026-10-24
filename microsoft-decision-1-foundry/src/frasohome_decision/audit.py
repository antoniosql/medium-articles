"""Offline audit of the human labels in the ticket extract.

Reproduces the article's finding: identical messages keep the same case type,
but their priority and sentiment labels disagree.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass


@dataclass
class LabelAudit:
    tickets: int
    repeated_texts: int
    rows_in_repeated_texts: int
    conflicting: dict[str, int]
    worst_example: tuple[str, Counter]


AUDITED_COLUMNS = ("tipo_caso", "prioridad", "sentimiento_inicial")


def audit_labels(tickets: list[dict[str, str]]) -> LabelAudit:
    groups: dict[str, list[dict[str, str]]] = defaultdict(list)
    for ticket in tickets:
        groups[ticket["texto_cliente"]].append(ticket)
    repeated = {text: rows for text, rows in groups.items() if len(rows) > 1}

    conflicting = {
        column: sum(1 for rows in repeated.values() if len({r[column] for r in rows}) > 1)
        for column in AUDITED_COLUMNS
    }
    text, rows = max(
        repeated.items(),
        key=lambda item: (len({r["prioridad"] for r in item[1]}), len(item[1])),
    )
    return LabelAudit(
        tickets=len(tickets),
        repeated_texts=len(repeated),
        rows_in_repeated_texts=sum(len(rows) for rows in repeated.values()),
        conflicting=conflicting,
        worst_example=(text, Counter(r["prioridad"] for r in rows)),
    )
