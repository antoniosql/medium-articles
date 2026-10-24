from frasohome_decision.audit import audit_labels
from frasohome_decision.data import load_tickets


def test_label_audit_reproduces_the_article_numbers():
    audit = audit_labels(load_tickets())
    assert audit.tickets == 560
    assert audit.repeated_texts == 43
    assert audit.rows_in_repeated_texts == 152
    assert audit.conflicting == {"tipo_caso": 0, "prioridad": 27, "sentimiento_inicial": 30}


def test_worst_example_is_the_loyalty_complaint():
    text, priorities = audit_labels(load_tickets()).worst_example
    assert "nivel de fidelización" in text
    assert sum(priorities.values()) == 16
    assert priorities == {"Alta": 3, "Media": 6, "Baja": 7}
