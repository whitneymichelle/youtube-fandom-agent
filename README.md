# YouTube Fandom Agent

A small project for collecting YouTube metadata, modeling it into SQLite, and answering questions about the collection using structured data plus comment evidence.

## What this repo does

- fetches YouTube metadata into raw JSON batches
- normalizes and models that data into SQLite tables for analysis
- answers factual questions such as counts, averages, category/topic breakdowns, and tag patterns
- looks at comment themes and context when a question depends on tone, discussion, or interpretation
- evaluates the agent against a live question set
- opens a visual HTML review dashboard after each eval run

## Project layout

```text
youtube-fandom-agent/
├── data/
│   ├── raw/            # raw YouTube API fetch batches
│   ├── curated/        # reviewed or curated artifacts
│   ├── processed/      # SQLite database and modeled outputs
│   └── comments_*      # optional generated comment exports
├── src/
│   ├── youtube_api/    # fetch + load logic
│   ├── agents/        # SQL-backed agent implementations
│   └── evaluation/    # eval runner + HTML review export
├── evals/
│   ├── questions.json  # active question set
│   └── results/        # generated eval output JSONL
├── tests/              # unit tests
├── docs/               # project docs and constraints
├── scripts/            # runnable fetch scripts
├── .gitignore
├── requirements.txt
├── Makefile
└── README.md
```

## Setup

```bash
cd youtube-fandom-agent
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

If you need local API config, create a `.env` file in the repo root with your YouTube key.

## Core workflow

1. fetch YouTube metadata into `data/raw/`
2. model the data into the SQLite layer under `data/processed/`
3. run the eval against the active question set
4. inspect the generated HTML review report
5. improve the questions, agent, or data model in small increments

## Run the eval

```bash
python -m src.evaluation.run_eval
```

This writes results to `evals/results/simple_sql_agent.jsonl`.

To generate and open the HTML dashboard after the run:

```bash
python -m src.evaluation.run_eval --open-report
```

To use a different results file and a different review output:

```bash
python -m src.evaluation.run_eval --output evals/results/my_run.jsonl --questions evals/questions.json
python -m src.evaluation.export_review --results evals/results/my_run.jsonl --review evals/reviews/my_review.html --overwrite
```

## Agent

The current baseline is a SQL-backed agent for structured questions, with comment evidence available for richer interpretation and theme analysis.

Example:

```bash
python -m src.agents.simple_sql_agent "How many videos are in the dataset?"
```

## Data boundaries

- `data/raw/`: raw fetch snapshots
- `data/curated/`: reviewed or curated source artifacts
- `data/processed/`: modeled SQLite tables used by the agent
- generated comments: supporting evidence for themes, tone, and context

## Contributing

1. keep the scope narrow
2. add tests for new behavior
3. run the eval before considering it ready
4. improve the question set and the agent without broadening the repo into a bigger platform

## Make commands

| Command | What it does |
|---|---|
| `make test` | Runs the pytest suite. |
| `make eval` | Runs the active question set and appends one snapshot to history, writing the current JSONL result. |
| `make eval-report` | Runs the eval, appends one snapshot to history, and creates timestamped JSONL and HTML report files. |
| `make history-report` | Rebuilds the HTML history dashboard from existing run snapshots; it does not append a run. |
| `make ask q="your question"` | Sends a question directly to the SQL agent. |
| `make clean-local` | Removes Python caches and pytest cache files. |
