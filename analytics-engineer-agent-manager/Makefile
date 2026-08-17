PYTHON ?= python

.PHONY: install validate plan test demo demo-fail clean

install:
	$(PYTHON) -m pip install -e ".[dev]"

validate:
	$(PYTHON) -m agent_manager validate

plan:
	$(PYTHON) -m agent_manager plan

test:
	$(PYTHON) -m pytest -q

demo:
	$(PYTHON) -m agent_manager demo

demo-fail:
	$(PYTHON) -m agent_manager demo --scenario unmapped_category

clean:
	rm -rf .data dbt_financialhome/target dbt_financialhome/logs outputs/agent_run_report.*
