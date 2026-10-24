import json

from conftest import ROOT

from frasohome_decision.data import load_draft, load_rules, load_tickets
from frasohome_decision.questions import (
    CASE_TYPES,
    guardrail_questions,
    triage_questions,
    triage_state,
)

VALID_TYPES = {"noul", "choice", "score"}


def test_case_types_cover_every_label_in_the_data():
    labels = {t["tipo_caso"] for t in load_tickets()}
    assert labels == set(CASE_TYPES)


def test_triage_questions_have_the_documented_shape():
    questions = triage_questions()
    assert {q["type"] for q in questions.values()} == VALID_TYPES
    assert isinstance(questions["case_type"]["criteria"], dict)
    assert questions["frustration"]["criteria"] == [
        "Calm",
        "Mildly annoyed",
        "Frustrated",
        "Angry",
    ]
    assert all(q["instructions"] for q in questions.values())


def test_triage_state_is_json_with_channel_and_message():
    ticket = load_tickets()[0]
    assert triage_state(ticket) == {
        "canal": ticket["canal_soporte"],
        "mensaje": ticket["texto_cliente"],
    }


def test_guardrails_one_noul_per_applicable_rule():
    rules = load_rules()
    assert len(rules) == 12
    email = guardrail_questions(rules, "email")
    assert len(email) == 11  # GR-011 is sms/push only
    assert "GR-011" not in email
    assert all(q["type"] == "noul" for q in email.values())
    sms = guardrail_questions(rules, "sms")
    assert "GR-010" not in sms and "GR-011" in sms  # GR-010 is email/chat/web only


def test_example_files_match_the_code():
    """examples/05 and 06 are what the CLI sends; keep them in sync."""
    triage = json.loads((ROOT / "examples/05-frasohome-triage.json").read_text("utf-8"))
    assert triage["questions"] == triage_questions()

    guard = json.loads((ROOT / "examples/06-frasohome-guardrails.json").read_text("utf-8"))
    draft = load_draft()
    assert guard["state"] == draft
    assert guard["questions"] == guardrail_questions(load_rules(), draft["canal"])


def test_every_example_is_a_valid_request():
    for path in sorted((ROOT / "examples").glob("*.json")):
        body = json.loads(path.read_text("utf-8"))
        assert body["model"] == "<deployment-name>", path.name
        assert "state" in body, path.name
        for name, question in body["questions"].items():
            assert question["type"] in VALID_TYPES, f"{path.name}:{name}"
            assert question["instructions"], f"{path.name}:{name}"
