"""Minimal client for the Microsoft-Decision-1 decision API in Microsoft Foundry.

POST {endpoint}/providers/microsoft/v1/systemone
{"model": <deployment name>, "state": <text or JSON>, "questions": {<name>: {...}}}

Only the standard library is used for HTTP, so the request on the wire is exactly
what the article shows. Authentication is Microsoft Entra ID by default
(DefaultAzureCredential), or an API key when AZURE_API_KEY is set.
"""

from __future__ import annotations

import json
import random
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from typing import Any

from frasohome_decision.config import Settings

TOKEN_SCOPE = "https://cognitiveservices.azure.com/.default"
RETRYABLE = {429, 500, 502, 503, 504}


class DecisionAPIError(RuntimeError):
    """The API returned an error or a response the demo cannot read."""


@dataclass
class Decision:
    """A parsed response. Field names follow the Learn quickstart and the System One
    contract; readers are defensive so a renamed field fails loudly, not silently."""

    raw: dict[str, Any]
    latency_ms: float = 0.0
    answers: dict[str, dict[str, Any]] = field(init=False)

    def __post_init__(self) -> None:
        answers = self.raw.get("answers")
        if not isinstance(answers, dict):
            raise DecisionAPIError(f"Response has no 'answers' object: {self.raw!r:.300}")
        self.answers = answers

    def _answer(self, name: str) -> dict[str, Any]:
        try:
            return self.answers[name]
        except KeyError as exc:
            raise DecisionAPIError(f"No answer named {name!r} in the response.") from exc

    def choice(self, name: str) -> str:
        value = self._answer(name).get("choice")
        if not isinstance(value, str):
            raise DecisionAPIError(f"Answer {name!r} has no 'choice'.")
        return value

    def probabilities(self, name: str) -> dict[str, float]:
        probs = self._answer(name).get("probabilities")
        return {k: float(v) for k, v in probs.items()} if isinstance(probs, dict) else {}

    def top_probability(self, name: str) -> float | None:
        probs = self.probabilities(name)
        if probs:
            return max(probs.values())
        confidence = self._answer(name).get("confidence")
        return float(confidence) if confidence is not None else None

    def noul(self, name: str) -> float:
        answer = self._answer(name)
        for key in ("noul", "probability"):
            if answer.get(key) is not None:
                return float(answer[key])
        raise DecisionAPIError(f"Answer {name!r} has no 'noul' probability.")

    def score(self, name: str) -> float:
        value = self._answer(name).get("score")
        if value is None:
            raise DecisionAPIError(f"Answer {name!r} has no 'score'.")
        return float(value)

    @property
    def input_tokens(self) -> int:
        usage = self.raw.get("usage") or {}
        return int(usage.get("input_tokens") or usage.get("prompt_tokens") or 0)


class DecisionClient:
    def __init__(self, settings: Settings, timeout: float = 60.0, retries: int = 4) -> None:
        self.settings = settings
        self.timeout = timeout
        self.retries = retries
        self._credential = None
        if not settings.api_key:
            from azure.identity import DefaultAzureCredential

            self._credential = DefaultAzureCredential()

    def _auth_headers(self) -> dict[str, str]:
        if self.settings.api_key:
            return {"api-key": self.settings.api_key}
        token = self._credential.get_token(TOKEN_SCOPE).token  # type: ignore[union-attr]
        return {"Authorization": f"Bearer {token}"}

    def post(self, body: dict[str, Any]) -> Decision:
        """Send a full request body. `model` is set to the deployment name."""
        payload = {**body, "model": self.settings.deployment}
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")

        for attempt in range(self.retries + 1):
            request = urllib.request.Request(
                self.settings.url,
                data=data,
                method="POST",
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                    **self._auth_headers(),
                },
            )
            start = time.perf_counter()
            try:
                with urllib.request.urlopen(request, timeout=self.timeout) as response:
                    raw = json.loads(response.read())
                return Decision(raw=raw, latency_ms=(time.perf_counter() - start) * 1000)
            except urllib.error.HTTPError as exc:
                if exc.code in RETRYABLE and attempt < self.retries:
                    retry_after = exc.headers.get("Retry-After") if exc.headers else None
                    delay = float(retry_after) if retry_after else 2**attempt + random.random()
                    time.sleep(min(delay, 30))
                    continue
                detail = exc.read().decode("utf-8", "replace")[:500]
                message = f"HTTP {exc.code} from {self.settings.url}: {detail}"
                raise DecisionAPIError(message) from exc
            except urllib.error.URLError as exc:
                message = f"Could not reach {self.settings.url}: {exc.reason}"
                raise DecisionAPIError(message) from exc
            except json.JSONDecodeError as exc:
                raise DecisionAPIError("The API returned invalid JSON.") from exc
        raise DecisionAPIError("Retries exhausted.")

    def decide(self, state: Any, questions: dict[str, Any]) -> Decision:
        return self.post({"state": state, "questions": questions})
