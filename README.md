# YouTube Fandom Agent

An LLM-powered agent that retrieves YouTube video data and answers increasingly complex questions about fandom topics, with an integrated evaluation system to track improvements across versions.

## Project Structure

```
youtube-fandom-agent/
├── data/
│   ├── raw/              # Original YouTube API batches
│   ├── curated/          # Human-reviewed labels or curated subsets
│   ├── processed/        # SQLite database and modeled outputs
│   ├── comments_full/    # Generated comment text exports (not committed)
│   └── comments_test/    # Smaller comment data slices for testing
├── src/
│   ├── youtube_api/      # YouTube API client and loader logic
│   ├── agents/           # Agent implementations
│   ├── evaluation/       # Eval workflow and review export tools
│   └── utils/            # Helper utilities
├── scripts/              # Runnable fetch entrypoints
├── notebooks/            # Jupyter notebooks for exploration
├── tests/                # Unit tests
├── docs/                 # Project documentation
├── requirements.txt      # Python dependencies
├── .gitignore            # Ignores generated data and local secrets
├── Makefile              # Common project commands
└── README.md             # Project overview
```

## Setup

1. **Clone and install dependencies:**
   ```bash
   cd youtube-fandom-agent
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Configure the YouTube API key locally:**
   ```bash
   echo "YOUTUBE_API_KEY=your-key" > .env
   ```
   The app reads this from the environment via `python-dotenv`.

3. **Start developing:**
   - Explore data fetching in `scripts/` and `notebooks/`
   - Build agent logic in `src/agents/`
   - Define evaluations in `src/evaluation/`

## Project Shape

This repo is intentionally simple: ship a useful baseline agent, collect real signals from the data, and improve it incrementally over time.

The current workflow is:
- collect YouTube metadata into `data/raw/`
- model it into a reliable SQLite layer under `data/processed/`
- keep curated judgment files in `data/curated/` when they are human-reviewed source artifacts
- add richer evidence as it becomes available, such as comment text exports in `data/comments_full/` or smaller test slices in `data/comments_test/`
- answer narrow structured questions with a deterministic SQL agent
- improve the agent without reworking the whole project into separate permanent phases

The important idea is not a formal "phase plan" but a continuous loop of better data, better prompts, better queries, and better evaluations.

## Data Layer Overview

This project keeps several kinds of data separate:

- `data/raw/`: raw JSON returned by the YouTube API; historical fetch snapshots
- `data/curated/`: smaller reviewed or curated label sets used for evaluation and relevance checks
- `data/processed/`: SQLite database and modeled tables used by the agent
- `data/comments_full/` and `data/comments_test/`: generated comment text exports; useful evidence, but not the same thing as the core modeled database

The curated label files and the processed SQLite tables are the versioned source artifacts. Generated comment JSONL exports are runtime artifacts and are intentionally kept out of git.

## Evaluation System

Track improvements across versions:
- Question complexity tiers
- Answer quality metrics
- Accuracy and relevance scores
- Performance benchmarks

Run the eval and export a review worksheet:

```bash
python -m src.evaluation.run_eval
python -m src.evaluation.export_review --human-only
```

Review files are protected by default so human notes are not overwritten. Use a
new `--review` path for a fresh run, or pass `--overwrite` only when replacing
the existing review is intentional.

## Simple SQL Agent

The first agent is a deterministic SQL-backed baseline. It answers supported
questions from the modeled SQLite tables and returns an answer, SQL, support
level, self-check, and limitations.

Run it with:

```bash
python -m src.agents.simple_sql_agent "How many videos are in the dataset?"
```

It is intentionally not a full RAG system yet. V1 uses SQL because many current
questions are structured metric questions: counts, averages, medians, category
breakdowns, tag counts, and topic counts.

The dataset already has semi-structured text fields, including titles,
descriptions, tags, channel names, categories, and topics. A later agent can use
those fields for lightweight inference or retrieval, especially for video-type
classification, theme discovery, and questions where the answer depends on
wording rather than numeric aggregation alone. RAG becomes more useful as the
project adds richer unstructured sources such as transcripts, comment text,
articles, notes, or human review examples.

## Contributing

1. Create feature branches
2. Add tests for new functionality
3. Run evaluation suite before committing
4. Document changes in `docs/`
