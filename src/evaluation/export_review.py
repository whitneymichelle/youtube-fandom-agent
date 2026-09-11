"""
Export JSONL eval results into a human-readable review Markdown file.
"""

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List


DEFAULT_RESULTS_PATH = "evals/results/simple_sql_agent_v1.jsonl"
DEFAULT_REVIEW_PATH = "evals/reviews/simple_sql_agent_v1_review.md"


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
    lines = [
        "# Simple SQL Agent V1 Review",
        "",
        f"Source results: `{results_path}`",
        "",
    ]
    lines.extend(render_summary(review_results, all_results))
    lines.extend(
        [
            "",
            "## Review Instructions",
            "",
            "Score each answer after reading the question, answer, SQL, self-check, and limitations.",
            "",
            "Scoring:",
            "",
            "- Correctness: `0` wrong/unsupported, `1` partially correct, `2` correct but thin, `3` correct and well-supported",
            "- Groundedness: `0` not grounded, `1` weakly grounded, `2` mostly grounded, `3` properly grounded in schema/results",
            "- Self-awareness: `0` overconfident/wrong, `1` vague, `2` mostly aware but incomplete, `3` accurately states support or limits",
            "",
            "When feedback reveals a recurring failure, update the relevant system artifact: `docs/schema.md`, `docs/semantic_model.md`, `docs/gotchas.md`, `docs/agent_rules.md`, eval questions, examples, agent code, or tests.",
            "",
        ]
    )

    for result in review_results:
        lines.extend(render_result(result))

    return "\n".join(lines).rstrip() + "\n"


def render_summary(
    review_results: List[Dict[str, Any]],
    all_results: List[Dict[str, Any]],
) -> List[str]:
    support_counts = count_by(all_results, "support_level")
    difficulty_counts = count_by(review_results, "difficulty")
    answer_type_counts = count_by(review_results, "answer_type")
    answered_with_sql = sum(1 for result in all_results if result["sql"])
    human_review_needed = sum(
        1 for result in all_results if result["needs_human_score"]
    )
    review_question_ids = ", ".join(result["question_id"] for result in review_results)

    lines = [
        "## Summary",
        "",
        f"- Total eval questions: `{len(all_results)}`",
        f"- Review items in this file: `{len(review_results)}`",
        f"- Human review needed: `{human_review_needed}`",
        f"- Answered with SQL: `{answered_with_sql}`",
        f"- Answered without SQL: `{len(all_results) - answered_with_sql}`",
        "",
        "Support levels:",
    ]
    lines.extend(
        f"- `{support_level}`: `{count}`"
        for support_level, count in support_counts.items()
    )

    lines.extend(["", "Review item difficulty:"])
    lines.extend(
        f"- `{difficulty}`: `{count}`"
        for difficulty, count in difficulty_counts.items()
    )

    lines.extend(["", "Review item answer types:"])
    lines.extend(
        f"- `{answer_type}`: `{count}`"
        for answer_type, count in answer_type_counts.items()
    )

    lines.extend(
        [
            "",
            f"Review question IDs: `{review_question_ids}`",
        ]
    )
    return lines


def count_by(records: List[Dict[str, Any]], key: str) -> Dict[str, int]:
    counts = {}
    for record in records:
        value = str(record.get(key))
        counts[value] = counts.get(value, 0) + 1
    return dict(sorted(counts.items()))


def render_result(result: Dict[str, Any]) -> List[str]:
    lines = [
        f"## {result['question_id']}: {result['question']}",
        "",
        f"- Difficulty: `{result['difficulty']}`",
        f"- Answer type: `{result['answer_type']}`",
        f"- Requires human review: `{result['requires_human_review']}`",
        f"- Support level: `{result['support_level']}`",
        "",
        "### Agent Answer",
        "",
        result["agent_answer"],
        "",
        "### SQL",
        "",
    ]

    if result["sql"]:
        lines.extend(["```sql", result["sql"].strip(), "```"])
    else:
        lines.append("No SQL used.")

    lines.extend(
        [
            "",
            "### Rows",
            "",
            "```json",
            json.dumps(result["rows"], ensure_ascii=False, indent=2),
            "```",
            "",
            "### Self-Check",
            "",
            result["self_check"],
            "",
            "### Limitations",
            "",
        ]
    )

    if result["limitations"]:
        lines.extend(f"- {limitation}" for limitation in result["limitations"])
    else:
        lines.append("- None stated.")

    if result.get("expected_limitation"):
        lines.extend(
            [
                "",
                "### Expected Limitation",
                "",
                result["expected_limitation"],
            ]
        )

    lines.extend(
        [
            "",
            "### Human Review",
            "",
            "- Correctness: ",
            "- Groundedness: ",
            "- Self-awareness: ",
            "- Notes: ",
            "- Follow-up artifact updates: ",
            "",
        ]
    )
    return lines


def print_summary(summary: Dict[str, Any]) -> None:
    print(f"Wrote review file to {summary['review_path']}")
    print(f"Source results: {summary['results_path']}")
    print(f"Total result rows: {summary['total_results']}")
    print(f"Review items: {summary['review_items']}")
    print(f"Human-only: {summary['human_only']}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Export eval JSONL to Markdown.")
    parser.add_argument(
        "--results",
        default=DEFAULT_RESULTS_PATH,
        help="Path to JSONL eval results",
    )
    parser.add_argument(
        "--review",
        default=DEFAULT_REVIEW_PATH,
        help="Path to write Markdown review file",
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
