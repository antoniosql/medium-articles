"""A local fake of the decision endpoint so every test runs offline.

The fake is deliberately dumb (keyword matching). It checks the request shape the
real API expects and answers in the documented response shape; it says nothing
about the real model's quality.
"""

from __future__ import annotations

import json
import os
import threading
from collections.abc import Iterator
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[1]
API_PATH = "/providers/microsoft/v1/systemone"
API_KEY = "test-key"
DEPLOYMENT = "frasohome-decision-test"

KEYWORDS = {
    "devolucion": ["devol", "reembolso", "abono"],
    "entrega": ["entrega", "envío", "seguimiento", "tránsito", "tarde"],
    "defecto": ["defecto", "daño", "dañado", "piezas", "acabado", "roto"],
    "stock_tienda": ["stock", "disponibilidad"],
    "cupon": ["cupón", "código", "promoc", "descuento"],
    "fidelizacion": ["puntos", "fidelización", "club", "nivel"],
    "info_producto": ["medidas", "espacio", "material", "dudas", "encaj"],
}
VIOLATED_RULES = {"GR-002", "GR-003", "GR-005", "GR-012"}


def _text(state: Any) -> str:
    return json.dumps(state, ensure_ascii=False).lower()


def fake_answer(name: str, question: dict[str, Any], state: Any) -> dict[str, Any]:
    text = _text(state)
    kind = question["type"]
    if kind == "choice":
        options = list(question["criteria"])
        hits = {o: sum(k in text for k in KEYWORDS.get(o, [o.lower()])) for o in options}
        best = max(options, key=lambda o: hits[o])
        top = 0.9 if hits[best] else 1 / len(options)
        rest = (1 - top) / (len(options) - 1)
        return {
            "type": "choice",
            "choice": best,
            "probabilities": {o: (top if o == best else rest) for o in options},
        }
    if kind == "score":
        levels = len(question["criteria"])
        return {"type": "score", "score": (levels - 1) * (0.8 if "!" in text else 0.3)}
    if kind == "noul":
        if name.startswith("GR-"):
            return {"type": "noul", "noul": 0.92 if name in VIOLATED_RULES else 0.08}
        blocked = any(k in text for k in ("defecto", "no puedo", "falla", "tarde"))
        return {"type": "noul", "noul": 0.9 if blocked else 0.2}
    raise ValueError(kind)


class FakeDecisionAPI(BaseHTTPRequestHandler):
    calls: list[dict[str, Any]] = []
    fail_next: list[int] = []

    def log_message(self, *args: Any) -> None:  # keep pytest output clean
        pass

    def _reply(self, status: int, body: dict[str, Any]) -> None:
        data = json.dumps(body).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        if status == 429:
            self.send_header("Retry-After", "0")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_POST(self) -> None:  # noqa: N802
        length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(length))
        FakeDecisionAPI.calls.append(
            {"path": self.path, "headers": {k.lower(): v for k, v in self.headers.items()}, **body}
        )
        if FakeDecisionAPI.fail_next:
            self._reply(FakeDecisionAPI.fail_next.pop(0), {"error": {"message": "simulated"}})
            return
        if self.path != API_PATH:
            self._reply(404, {"error": {"message": "not found"}})
            return
        if self.headers.get("api-key") != API_KEY:
            self._reply(401, {"error": {"message": "unauthorized"}})
            return
        if body.get("model") != DEPLOYMENT or "state" not in body or not body.get("questions"):
            self._reply(400, {"error": {"message": "bad request"}})
            return
        answers = {
            name: fake_answer(name, q, body["state"]) for name, q in body["questions"].items()
        }
        self._reply(
            200,
            {
                "model": "microsoft-decision-1",
                "answers": answers,
                "usage": {"input_tokens": 100 + 20 * len(answers), "output_tokens": 0},
            },
        )


@pytest.fixture()
def fake_api(monkeypatch: pytest.MonkeyPatch) -> Iterator[type[FakeDecisionAPI]]:
    FakeDecisionAPI.calls = []
    FakeDecisionAPI.fail_next = []
    server = ThreadingHTTPServer(("127.0.0.1", 0), FakeDecisionAPI)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    monkeypatch.setenv("AZURE_ENDPOINT", f"http://127.0.0.1:{server.server_port}")
    monkeypatch.setenv("DEPLOYMENT_NAME", DEPLOYMENT)
    monkeypatch.setenv("AZURE_API_KEY", API_KEY)
    for proxy_bypass in ("NO_PROXY", "no_proxy"):  # never send the fake's traffic to a proxy
        monkeypatch.setenv(proxy_bypass, "127.0.0.1,localhost")
    try:
        yield FakeDecisionAPI
    finally:
        server.shutdown()
        server.server_close()


@pytest.fixture(autouse=True)
def run_from_project_root(monkeypatch: pytest.MonkeyPatch) -> None:
    """CLI defaults point at ./data; tests run from the project root like a user would."""
    monkeypatch.chdir(ROOT)
    for name in ("AZURE_ENDPOINT", "DEPLOYMENT_NAME", "AZURE_API_KEY"):
        if name in os.environ:
            monkeypatch.delenv(name)
