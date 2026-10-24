"""The typed questions used in the article.

Pattern 1 (ticket triage) ports TypeSafe's Jev quickstart: one call, three questions
(Choice + Score + Noul) about the same support message.

Pattern 2 (brand guardrails) ports the pi-warden guardrail: several Noul questions
checked before an action, here one per FraSoHome brand rule.
"""

from __future__ import annotations

from typing import Any

# Keys match the `tipo_caso` label in data/support_tickets.csv, so accuracy can be measured.
CASE_TYPES: dict[str, str] = {
    "devolucion": (
        "Return or refund of an item already purchased: return status, "
        "refund not received, return paperwork"
    ),
    "info_producto": (
        "Pre-purchase product question: dimensions, materials, "
        "fit in the customer's space, alternatives"
    ),
    "entrega": "Delivery of an order: late, in transit, tracking, delivery date mismatch",
    "defecto": "Product arrived damaged, defective, with missing parts or a finishing problem",
    "stock_tienda": (
        "Stock availability of a product in a physical store or unclear availability on the website"
    ),
    "cupon": "Promo code, coupon or campaign discount that fails or was not applied",
    "fidelizacion": "Loyalty programme: points, tier, club benefits not showing",
}

FRUSTRATION_LEVELS = ["Calm", "Mildly annoyed", "Frustrated", "Angry"]


def triage_questions() -> dict[str, Any]:
    return {
        "case_type": {
            "type": "choice",
            "instructions": (
                "FraSoHome is a home furniture and decor retailer. Which support queue "
                "should handle this customer message? Pick the primary problem."
            ),
            "criteria": dict(CASE_TYPES),
        },
        "frustration": {
            "type": "score",
            "instructions": "How frustrated does the customer sound in this message?",
            "criteria": list(FRUSTRATION_LEVELS),
        },
        "is_blocked": {
            "type": "noul",
            "instructions": (
                "Is the customer currently unable to use a product or complete a "
                "purchase until FraSoHome acts?"
            ),
            "criteria": {
                "true": "Something is broken, missing, late or blocking a purchase right now",
                "false": "An informational question or a status check with no blocker",
            },
        },
    }


def triage_state(ticket: dict[str, str]) -> dict[str, str]:
    """JSON state: the channel travels with the message."""
    return {"canal": ticket["canal_soporte"], "mensaje": ticket["texto_cliente"]}


def rule_applies(rule: dict[str, str], channel: str) -> bool:
    channels = [c.strip() for c in rule["aplica_a_canal"].split(",")]
    return "all" in channels or channel in channels


def guardrail_questions(rules: list[dict[str, str]], channel: str) -> dict[str, Any]:
    """One Noul per applicable rule, generated from the CSV so rules change without code."""
    return {
        rule["regla_id"]: {
            "type": "noul",
            "instructions": (
                "Does this marketing draft VIOLATE the following FraSoHome brand rule? "
                f"Rule: {rule['descripcion_regla']}"
            ),
        }
        for rule in rules
        if rule_applies(rule, channel)
    }
