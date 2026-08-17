.PHONY: test run gate clean

test:
	pytest

run:
	python -m local_demo.cli run --data data/customers.csv --rules rules/quality_rules.yml --tag silver_hygiene --mode drop

gate:
	python -m local_demo.cli gate --baseline data/baseline_metrics.json --actual artifacts/latest_metrics.json

clean:
	rm -rf artifacts .pytest_cache
