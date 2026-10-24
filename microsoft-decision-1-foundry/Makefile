PYTHON ?= python

.PHONY: install test lint deploy smoke audit triage guardrails dry-run teardown clean

install:
	$(PYTHON) -m pip install -e ".[dev]"

test:
	$(PYTHON) -m pytest -q

lint:
	$(PYTHON) -m ruff check src tests

# Azure: creates resource group, Foundry resource, project and the Decision-1 deployment
deploy:
	bash infra/scripts/deploy.sh

teardown:
	bash infra/scripts/teardown.sh

# Offline: reproduces the label-consistency numbers quoted in the article
audit:
	decision-demo audit-labels

# Offline: prints the exact requests without calling the endpoint
dry-run:
	decision-demo triage --dry-run
	decision-demo guardrails --dry-run

# Online: needs a deployment and a .env
smoke:
	decision-demo send examples/02-choice.json

triage:
	decision-demo triage --limit 100

guardrails:
	decision-demo guardrails

clean:
	rm -rf .pytest_cache .ruff_cache outputs/triage_decisions.csv outputs/*.json
