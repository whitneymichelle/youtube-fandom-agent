"""
Export JSONL eval results into a simple HTML dashboard for human review.
"""

import argparse
import json
from html import escape
from pathlib import Path
from typing import Any, Dict, List


DEFAULT_RESULTS_PATH = "evals/results/simple_sql_agent.jsonl"
DEFAULT_REVIEW_PATH = "evals/reviews/simple_sql_agent_review.html"


def load_jsonl(path: str) -> List[Dict[str, Any]]:
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def export_review(
    results_path: str = DEFAULT_RESULTS_PATH,
    review_path: str = DEFAULT_REVIEW_PATH,
    human_only: bool = False,
    overwrite: bool = False,
) -> Dict[str, Any]:
    results = load_jsonl(results_path)
    if human_only:
        review_results = [row for row in results if row["needs_human_score"]]
    else:
        review_results = results

    output_path = Path(review_path)
    if output_path.exists() and not overwrite:
        raise FileExistsError(
            f"Review file already exists: {review_path}. "
            "Use --overwrite to replace it, or choose a new --review path."
        )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        render_review(review_results, results, results_path),
        encoding="utf-8",
    )

    return {
        "results_path": results_path,
        "review_path": review_path,
        "total_results": len(results),
        "review_items": len(review_results),
        "human_only": human_only,
        "overwrite": overwrite,
    }


def render_review(
    review_results: List[Dict[str, Any]],
    all_results: List[Dict[str, Any]],
    results_path: str,
) -> str:
    summary_html = render_summary(review_results, all_results)
    cards_html = "\n".join(render_result(result) for result in review_results)

    return f"""<!DOCTYPE html>
<html lang=\"en\">
<head>
  <meta charset=\"utf-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
  <title>Simple SQL Agent Review</title>
  <style>
    :root {{
      --bg: #f6f8fb;
      --panel: #ffffff;
      --border: #dfe6ee;
      --text: #182230;
      --muted: #5c6d82;
      --primary: #2563eb;
      --supported: #166534;
      --unsupported: #991b1b;
      --partial: #92400e;
      --card-shadow: 0 8px 18px rgba(15, 23, 42, 0.08);
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      background: var(--bg);
      color: var(--text);
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
      line-height: 1.5;
    }}
    .container {{ max-width: 1200px; margin: 0 auto; padding: 32px 20px 64px; }}
    h1 {{ margin-bottom: 8px; }}
    .meta {{ color: var(--muted); margin-bottom: 24px; }}
    .summary-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
      gap: 16px;
      margin-bottom: 28px;
    }}
    .stat {{
      background: var(--panel);
      border: 1px solid var(--border);
      border-radius: 14px;
      padding: 18px 16px;
      box-shadow: var(--card-shadow);
    }}
    .stat-label {{ font-size: 12px; text-transform: uppercase; letter-spacing: 0.08em; color: var(--muted); }}
    .stat-value {{ font-size: 28px; font-weight: 700; margin-top: 6px; }}
    .panel {{
      background: var(--panel);
      border: 1px solid var(--border);
      border-radius: 16px;
      padding: 20px;
      box-shadow: var(--card-shadow);
      margin-top: 18px;
    }}
    .badge {{
      display: inline-block;
      padding: 4px 8px;
      border-radius: 999px;
      font-size: 12px;
      font-weight: 700;
      margin-right: 8px;
    }}
    .supported {{ background: #dcfce7; color: var(--supported); }}
    .unsupported {{ background: #fee2e2; color: var(--unsupported); }}
    .partially_supported {{ background: #fef3c7; color: var(--partial); }}
    .result-card {{
      background: var(--panel);
      border: 1px solid var(--border);
      border-radius: 16px;
      padding: 20px;
      margin-top: 22px;
      box-shadow: var(--card-shadow);
    }}
    .result-header {{
      display: flex;
      justify-content: space-between;
      gap: 16px;
      align-items: center;
      flex-wrap: wrap;
      border-bottom: 1px solid var(--border);
      padding-bottom: 12px;
      margin-bottom: 12px;
    }}
    .meta-list {{ color: var(--muted); display: flex; flex-wrap: wrap; gap: 12px; font-size: 14px; }}
    pre {{
      white-space: pre-wrap;
      word-break: break-word;
      background: #0f172a;
      color: #e2e8f0;
      padding: 14px;
      border-radius: 10px;
      font-size: 13px;
      overflow-x: auto;
    }}
    .section {{ margin-top: 20px; }}
    .section h3 {{ margin-bottom: 8px; font-size: 16px; }}
    .limitations {{ margin: 0; padding-left: 18px; }}
    a {{ color: var(--primary); }}
  </style>
</head>
<body>
  <div class=\"container\">
    <h1>Simple SQL Agent Review</h1>
    <div class=\"meta\">Source results: {escape(results_path)}</div>
    {summary_html}
    <div class=\"panel\">
      <h2>Review weak cases</h2>
      <p>Use this dashboard to inspect unsupported, partially supported, and human-review-needed questions.</p>
    </div>
    {cards_html}
  </div>
</body>
</html>
"""


def render_summary(
    review_results: List[Dict[str, Any]],
    all_results: List[Dict[str, Any]],
) -> str:
    support_counts = count_by(all_results, "support_level")
    difficulty_counts = count_by(review_results, "difficulty")
    answer_type_counts = count_by(review_results, "answer_type")
    answered_with_sql = sum(1 for result in all_results if result["sql"])
    human_review_needed = sum(
        1 for result in all_results if result["needs_human_score"]
    )

    def stat(label: str, value: str) -> str:
        return f"""
        <div class=\"stat\">
          <div class=\"stat-label\">{escape(label)}</div>
          <div class=\"stat-value\">{escape(value)}</div>
        </div>
        """

    rows = [
        stat("Total eval questions", str(len(all_results))),
        stat("Review items", str(len(review_results))),
        stat("Human review needed", str(human_review_needed)),
        stat("Answered with SQL", str(answered_with_sql)),
    ]

    support_markup = "".join(
        f"<span class=\"badge {escape(str(support).lower())}\">{escape(str(support))}: {count}</span>"
        for support, count in support_counts.items()
    )
    difficulty_markup = "".join(
        f"<span class=\"badge supported\">{escape(str(level))}: {count}</span>"
        for level, count in difficulty_counts.items()
    )
    answer_type_markup = "".join(
        f"<span class=\"badge supported\">{escape(str(answer_type))}: {count}</span>"
        for answer_type, count in answer_type_counts.items()
    )

    return f"""
    <div class=\"summary-grid\">
      {''.join(rows)}
    </div>
    <div class=\"panel\">
      <h2>Summary</h2>
      <p><strong>Support levels:</strong> {support_markup}</p>
      <p><strong>Review difficulty:</strong> {difficulty_markup}</p>
      <p><strong>Answer types:</strong> {answer_type_markup}</p>
    </div>
    """


def count_by(records: List[Dict[str, Any]], key: str) -> Dict[str, int]:
    counts = {}
    for record in records:
        value = str(record.get(key))
        counts[value] = counts.get(value, 0) + 1
    return dict(sorted(counts.items()))


def render_llm_evidence(result: Dict[str, Any]) -> str:
    if result.get("grading_method") != "llm":
        return ""

    evidence_stats = []
    for label, field in (("Comments retrieved", "comments_retrieved"), ("Comments used", "comments_used")):
        if field in result:
            evidence_stats.append(f"<span>{escape(label)}: {escape(str(result[field]))}</span>")

    scores = []
    for label, field in (
        ("Groundedness", "groundedness"),
        ("Interpretation quality", "interpretation_quality"),
        ("Limitations", "limitations_score"),
    ):
        if field in result:
            scores.append(
                f"<span class=\"badge supported\">{escape(label)}: {escape(str(result[field]))}/5</span>"
            )

    sample_ids = result.get("sample_comment_ids") or []
    sample_html = "".join(f"<li>{escape(str(comment_id))}</li>" for comment_id in sample_ids)

    can_html = "".join(
        f"<li>{escape(str(item))}</li>" for item in (result.get("can_determine") or [])
    )
    cannot_html = "".join(
        f"<li>{escape(str(item))}</li>" for item in (result.get("cannot_determine") or [])
    )

    return f"""
      <div class="section">
        <h3>LLM grading</h3>
        <div class="meta-list">{''.join(evidence_stats)}</div>
        <p>{''.join(scores)}</p>
      </div>
      <div class="section">
        <h3>Judge reasoning</h3>
        <p>{escape(str(result.get('judge_reasoning', 'Not yet graded.')))}</p>
      </div>
      <div class="section">
        <h3>Representative comment IDs</h3>
        <ul class="limitations">{sample_html or '<li>None provided.</li>'}</ul>
      </div>
      <div class="section">
        <h3>What can be determined</h3>
        <ul class="limitations">{can_html or '<li>Not yet identified.</li>'}</ul>
      </div>
      <div class="section">
        <h3>What cannot be determined</h3>
        <ul class="limitations">{cannot_html or '<li>Not yet identified.</li>'}</ul>
      </div>
    """


def render_result(result: Dict[str, Any]) -> str:
    support_class = str(result.get("support_level", "unsupported")).lower()
    limitations = result.get("limitations") or []
    limitations_html = "".join(
        f"<li>{escape(str(item))}</li>" for item in limitations
    ) or "<li>None stated.</li>"
    rows_json = json.dumps(result.get("rows", []), ensure_ascii=False, indent=2)
    sql = result.get("sql") or "No SQL used."

    llm_evidence_html = render_llm_evidence(result)
    human_review_reasons = result.get("human_review_reasons") or []
    human_review_reasons_html = "".join(
        f"<li>{escape(str(reason))}</li>" for reason in human_review_reasons
    ) or "<li>No automatic review trigger.</li>"

    return f"""
    <div class=\"result-card\">
      <div class=\"result-header\">
        <h2>{escape(str(result['question_id']))}: {escape(str(result['question']))}</h2>
        <div class=\"badge {escape(support_class)}\">{escape(str(result.get('support_level', 'unsupported')))}</div>
      </div>
      <div class=\"meta-list\">
        <span>Difficulty: {escape(str(result.get('difficulty', 'unknown')))}</span>
        <span>Answer type: {escape(str(result.get('answer_type', 'unknown')))}</span>
        <span>Human review: {escape(str(result.get('requires_human_review', False)))}</span>
      </div>

      <div class=\"section\">
        <h3>Agent answer</h3>
        <p>{escape(str(result.get('agent_answer', '')))}</p>
      </div>

      <div class=\"section\">
        <h3>SQL</h3>
        <pre>{escape(str(sql))}</pre>
      </div>

      <div class=\"section\">
        <h3>Rows</h3>
        <pre>{escape(rows_json)}</pre>
      </div>

      <div class=\"section\">
        <h3>Self-check</h3>
        <p>{escape(str(result.get('self_check', '')))}</p>
      </div>

      <div class=\"section\">
        <h3>Limitations</h3>
        <ul class=\"limitations\">{limitations_html}</ul>
      </div>

      {llm_evidence_html}
      <div class="section">
        <h3>Human review reasons</h3>
        <ul class="limitations">{human_review_reasons_html}</ul>
      </div>
    </div>
    """


def print_summary(summary: Dict[str, Any]) -> None:
    print(f"Wrote review file to {summary['review_path']}")
    print(f"Source results: {summary['results_path']}")
    print(f"Total result rows: {summary['total_results']}")
    print(f"Review items: {summary['review_items']}")
    print(f"Human-only: {summary['human_only']}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Export eval JSONL to an HTML review dashboard.")
    parser.add_argument(
        "--results",
        default=DEFAULT_RESULTS_PATH,
        help="Path to JSONL eval results",
    )
    parser.add_argument(
        "--review",
        default=DEFAULT_REVIEW_PATH,
        help="Path to write HTML review file",
    )
    parser.add_argument(
        "--human-only",
        action="store_true",
        help="Only include questions marked as needing human review",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Replace the review file if it already exists",
    )
    args = parser.parse_args()

    summary = export_review(
        results_path=args.results,
        review_path=args.review,
        human_only=args.human_only,
        overwrite=args.overwrite,
    )
    print_summary(summary)


if __name__ == "__main__":
    main()
