.PHONY: test eval review review-overwrite ask clean-local

PYTHON := venv/bin/python
PYTEST := venv/bin/pytest
DB ?= data/processed/youtube_fandom.db
QUESTIONS ?= evals/questions.json
RESULTS ?= evals/results/simple_sql_agent.jsonl
REVIEW ?= evals/reviews/simple_sql_agent_review.html

test:
	$(PYTEST)

eval:
	$(PYTHON) -m src.evaluation.run_eval --questions "$(QUESTIONS)" --output "$(RESULTS)" --db "$(DB)"

review:
	$(PYTHON) -m src.evaluation.run_eval --questions "$(QUESTIONS)" --output "$(RESULTS)" --db "$(DB)"
	$(PYTHON) -m src.evaluation.export_review --results "$(RESULTS)" --review "$(REVIEW)"

review-overwrite:
	$(PYTHON) -m src.evaluation.run_eval --questions "$(QUESTIONS)" --output "$(RESULTS)" --db "$(DB)"
	$(PYTHON) -m src.evaluation.export_review --results "$(RESULTS)" --review "$(REVIEW)" --overwrite

ask:
	$(PYTHON) -m src.agents.simple_sql_agent "$(q)"

clean-local:
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
	rm -rf .pytest_cache
