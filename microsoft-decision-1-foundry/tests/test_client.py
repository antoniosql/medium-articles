import pytest
from conftest import API_PATH, DEPLOYMENT

from frasohome_decision.client import DecisionAPIError, DecisionClient
from frasohome_decision.config import Settings
from frasohome_decision.questions import triage_questions


def client() -> DecisionClient:
    return DecisionClient(Settings.from_env(), timeout=5, retries=2)


def test_request_shape_and_auth(fake_api):
    decision = client().decide(
        {"canal": "Chat", "mensaje": "El cupón no funciona"},
        {"q": {"type": "noul", "instructions": "Is it about a coupon?"}},
    )
    call = fake_api.calls[-1]
    assert call["path"] == API_PATH
    assert call["model"] == DEPLOYMENT  # deployment name, not model name
    assert call["headers"]["api-key"] == "test-key"
    assert call["headers"]["content-type"] == "application/json"
    assert 0 <= decision.noul("q") <= 1
    assert decision.input_tokens > 0
    assert decision.latency_ms > 0


def test_post_overrides_the_placeholder_model(fake_api):
    client().post({"model": "<deployment-name>", "state": "x", "questions": triage_questions()})
    assert fake_api.calls[-1]["model"] == DEPLOYMENT


def test_three_question_types_in_one_call(fake_api):
    decision = client().decide(
        {"canal": "WhatsApp", "mensaje": "El sofá llegó con un defecto y no puedo usarlo!"},
        triage_questions(),
    )
    assert decision.choice("case_type") == "defecto"
    assert 0 <= decision.score("frustration") <= 3
    assert decision.noul("is_blocked") > 0.5
    assert len(fake_api.calls) == 1


def test_retries_on_429_then_succeeds(fake_api):
    fake_api.fail_next = [429]
    decision = client().decide("x", {"q": {"type": "noul", "instructions": "?"}})
    assert "q" in decision.answers
    assert len(fake_api.calls) == 2


def test_client_errors_are_not_retried(fake_api):
    fake_api.fail_next = [400]
    with pytest.raises(DecisionAPIError, match="HTTP 400"):
        client().decide("x", {"q": {"type": "noul", "instructions": "?"}})
    assert len(fake_api.calls) == 1


def test_settings_require_endpoint_and_deployment():
    with pytest.raises(SystemExit, match="AZURE_ENDPOINT"):
        Settings.from_env()


def test_settings_url():
    settings = Settings(endpoint="https://x.services.ai.azure.com/", deployment="d")
    assert settings.url == "https://x.services.ai.azure.com/providers/microsoft/v1/systemone"


def test_entra_token_is_cached_across_requests(fake_api, monkeypatch):
    """One credential call for many requests, refreshed only near expiry."""
    import time

    from azure.core.credentials import AccessToken

    class CountingCredential:
        calls = 0

        def get_token(self, *scopes):
            CountingCredential.calls += 1
            return AccessToken(f"token-{CountingCredential.calls}", int(time.time()) + 3600)

    monkeypatch.delenv("AZURE_API_KEY")
    c = DecisionClient(Settings.from_env(), timeout=5)
    c._credential = CountingCredential()
    for _ in range(3):
        c._auth_headers()
    assert CountingCredential.calls == 1

    c._token = AccessToken("almost-expired", int(time.time()) + 60)
    assert c._auth_headers() == {"Authorization": "Bearer token-2"}
