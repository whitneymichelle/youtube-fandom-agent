.PHONY: test eval review review-overwrite ask clean-local

PYTHON := venv/bin/python
PYTEST := venv/bin/pytest
DB ?= data/processed/youtube_fandom.db
QUESTIONS ?= evals/questions_v1.json
RESULTS ?= evals/results/simple_sql_agent_v1.jsonl
REVIEW ?= evals/reviews/simple_sql_agent_v1_review.md

test:
	$(PYTEST)

eval:
	$(PYTHON) -m src.evaluation.run_eval --questions "$(QUESTIONS)" --output "$(RESULTS)" --db "$(DB)"

review:
	$(PYTHON) -m src.evaluation.export_review --human-only --results "$(RESULTS)" --review "$(REVIEW)"

review-overwrite:
	$(PYTHON) -m src.evaluation.export_review --human-only --results "$(RESULTS)" --review "$(REVIEW)" --overwrite

ask:
	$(PYTHON) -m src.agents.simple_sql_agent "$(q)"

clean-local:
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
	rm -rf .pytest_cache
