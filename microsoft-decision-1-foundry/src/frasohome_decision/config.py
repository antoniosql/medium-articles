"""Settings from environment variables, with an optional .env file."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def load_env_file(path: Path) -> None:
    """Load KEY=VALUE lines into os.environ without overriding existing variables."""
    if not path.is_file():
        return
    for raw in path.read_text(encoding="utf-8-sig").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key, value = key.strip(), value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


@dataclass(frozen=True)
class Settings:
    endpoint: str
    deployment: str
    api_key: str | None = None

    @property
    def url(self) -> str:
        return f"{self.endpoint.rstrip('/')}/providers/microsoft/v1/systemone"

    @classmethod
    def from_env(cls) -> Settings:
        endpoint = os.environ.get("AZURE_ENDPOINT", "").strip()
        deployment = os.environ.get("DEPLOYMENT_NAME", "").strip()
        missing = [
            name
            for name, value in (("AZURE_ENDPOINT", endpoint), ("DEPLOYMENT_NAME", deployment))
            if not value
        ]
        if missing:
            raise SystemExit(
                f"Missing {', '.join(missing)}. Run infra/scripts/deploy.sh (or deploy.ps1), "
                "or copy .env.example to .env and fill it in."
            )
        return cls(
            endpoint=endpoint,
            deployment=deployment,
            api_key=os.environ.get("AZURE_API_KEY", "").strip() or None,
        )
