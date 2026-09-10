# YouTube Fandom Agent

An LLM-powered agent that retrieves YouTube video data and answers increasingly complex questions about fandom topics, with an integrated evaluation system to track improvements across versions.

## Project Structure

```
youtube-fandom-agent/
├── data/
│   ├── raw/              # YouTube API responses
│   └── processed/        # Cleaned and prepared data
├── src/
│   ├── youtube_api/      # YouTube data fetching
│   ├── agents/           # LLM agent implementations
│   ├── evaluation/       # Evaluation framework
│   └── utils/            # Helper utilities
├── notebooks/            # Jupyter notebooks for exploration
├── tests/                # Unit tests
├── docs/                 # Project documentation
├── config.example.py     # Example configuration
└── requirements.txt      # Python dependencies
```

## Setup

1. **Clone and install dependencies:**
   ```bash
   cd youtube-fandom-agent
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Configure API keys:**
   ```bash
   cp config.example.py config.py
   # Edit config.py with your YouTube API key
   ```

3. **Start developing:**
   - Explore data fetching in `notebooks/`
   - Build agent logic in `src/agents/`
   - Define evaluations in `src/evaluation/`

## Development Phases

### Phase 1: Data Collection
- Fetch YouTube videos via API
- Store raw data in structured format
- Explore and clean the data

### Phase 2: Basic Agent
- Implement simple question-answering agent
- Basic retrieval and generation
- Initial evaluation metrics

### Phase 3: Enhanced Agent
- Add more sophisticated reasoning
- Improve context handling
- Expand evaluation dataset

### Phase 4: Advanced Capabilities
- Multi-agent systems
- Complex reasoning chains
- Comprehensive evaluation framework

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
