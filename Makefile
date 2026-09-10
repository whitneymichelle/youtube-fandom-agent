.PHONY: test eval review review-overwrite ask clean-local

PYTHON := venv/bin/python
PYTEST := venv/bin/pytest

test:
	$(PYTEST)

eval:
	$(PYTHON) -m src.evaluation.run_eval

review:
	$(PYTHON) -m src.evaluation.export_review --human-only

review-overwrite:
	$(PYTHON) -m src.evaluation.export_review --human-only --overwrite

ask:
	$(PYTHON) -m src.agents.simple_sql_agent "$(q)"

clean-local:
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
	rm -rf .pytest_cache
