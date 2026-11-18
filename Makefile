.PHONY: test eval eval-report history-report ask clean-local

PYTHON := venv/bin/python
PYTEST := venv/bin/pytest
DB ?= data/processed/youtube_fandom.db
QUESTIONS ?= evals/questions.json
RESULTS ?= evals/results/simple_sql_agent.jsonl
HISTORY ?= evals/history/runs.jsonl
HISTORY_REVIEW ?= evals/reviews/eval_history.html
RUN_SUFFIX := $(shell date -u +%Y%m%d)-$(shell $(PYTHON) -c 'import uuid; print(uuid.uuid4().hex[:8])')
TIMESTAMPED_RESULTS ?= evals/results/simple_sql_agent_$(RUN_SUFFIX).jsonl
TIMESTAMPED_REVIEW ?= evals/reviews/simple_sql_agent_$(RUN_SUFFIX)_review.html

test:
	$(PYTEST)

eval:
	$(PYTHON) -m src.evaluation.run_eval --questions "$(QUESTIONS)" --output "$(RESULTS)" --db "$(DB)" --history "$(HISTORY)"

eval-report:
	$(PYTHON) -m src.evaluation.run_eval --questions "$(QUESTIONS)" --output "$(TIMESTAMPED_RESULTS)" --db "$(DB)" --history "$(HISTORY)"
	$(PYTHON) -m src.evaluation.export_review --results "$(TIMESTAMPED_RESULTS)" --review "$(TIMESTAMPED_REVIEW)"

history-report:
	$(PYTHON) -m src.evaluation.export_history --history "$(HISTORY)" --output "$(HISTORY_REVIEW)"

ask:
	$(PYTHON) -m src.agents.simple_sql_agent "$(q)"

clean-local:
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
	rm -rf .pytest_cache
