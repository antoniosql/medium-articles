# Contributing

This repository is designed as a compact reference implementation. Contributions should keep the control plane understandable and the demo runnable on a laptop.

## Principles

- Prefer explicit contracts over hidden prompt behavior.
- Keep business evaluation separate from SQL compilation.
- Do not add a production connector or real credential.
- Add a test for every change to contract validation or planning behavior.
- Preserve the expected-failure scenario.

## Local checks

```bash
python -m pip install -e ".[dev]"
python -m pytest -q
python -m agent_manager validate
python -m agent_manager demo
```

All contributions require human review. The example agent is not allowed to merge its own changes.
