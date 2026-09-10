"""
Run an eval question set against the deterministic SQL agent.
"""

from dataclasses import asdict
import argparse
import json
from pathlib import Path
from typing import Any, Dict, List

from src.agents.simple_sql_agent import SimpleSQLAgent


DEFAULT_QUESTIONS_PATH = "evals/questions_v1.json"
DEFAULT_OUTPUT_PATH = "evals/results/simple_sql_agent_v1.jsonl"
DEFAULT_DB_PATH = "data/processed/heated_rivalry.db"


def load_questions(path: str) -> List[Dict[str, Any]]:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def write_jsonl(path: str, records: List[Dict[str, Any]]) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")


def run_eval(
    questions_path: str = DEFAULT_QUESTIONS_PATH,
    output_path: str = DEFAULT_OUTPUT_PATH,
    db_path: str = DEFAULT_DB_PATH,
) -> Dict[str, Any]:
    questions = load_questions(questions_path)
    agent = SimpleSQLAgent(db_path)
    results = []

    for question in questions:
        response = agent.answer(question["question"])
        response_data = asdict(response)
        results.append(
            {
                "question_id": question["id"],
                "question": question["question"],
                "difficulty": question.get("difficulty"),
                "answer_type": question.get("answer_type"),
                "requires_human_review": question.get(
                    "requires_human_review",
                    True,
                ),
                "expected_tables": question.get("expected_tables", []),
                "expected_metrics": question.get("expected_metrics", []),
                "expected_dimensions": question.get("expected_dimensions", []),
                "expected_limitation": question.get("expected_limitation"),
                "agent": "simple_sql_agent",
                "agent_answer": response_data["answer"],
                "sql": response_data["sql"],
                "rows": response_data["rows"],
                "support_level": response_data["support_level"],
                "self_check": response_data["self_check"],
                "limitations": response_data["limitations"],
                "needs_human_score": question.get("requires_human_review", True),
            }
        )

    write_jsonl(output_path, results)
    return summarize_results(results, output_path)


def summarize_results(
    results: List[Dict[str, Any]],
    output_path: str,
) -> Dict[str, Any]:
    support_counts = count_by(results, "support_level")
    difficulty_counts = count_by(results, "difficulty")
    answer_type_counts = count_by(results, "answer_type")
    sql_count = sum(1 for row in results if row["sql"])
    human_review_count = sum(1 for row in results if row["needs_human_score"])

    return {
        "output_path": output_path,
        "total_questions": len(results),
        "answered_with_sql": sql_count,
        "answered_without_sql": len(results) - sql_count,
        "human_review_needed": human_review_count,
        "support_counts": support_counts,
        "difficulty_counts": difficulty_counts,
        "answer_type_counts": answer_type_counts,
    }


def count_by(records: List[Dict[str, Any]], key: str) -> Dict[str, int]:
    counts = {}
    for record in records:
        value = str(record.get(key))
        counts[value] = counts.get(value, 0) + 1
    return dict(sorted(counts.items()))


def print_summary(summary: Dict[str, Any]) -> None:
    print(f"Wrote results to {summary['output_path']}")
    print(f"Total questions: {summary['total_questions']}")
    print(f"Answered with SQL: {summary['answered_with_sql']}")
    print(f"Answered without SQL: {summary['answered_without_sql']}")
    print(f"Human review needed: {summary['human_review_needed']}")

    print("\nSupport levels:")
    for support_level, count in summary["support_counts"].items():
        print(f"  {support_level}: {count}")

    print("\nDifficulty:")
    for difficulty, count in summary["difficulty_counts"].items():
        print(f"  {difficulty}: {count}")

    print("\nAnswer types:")
    for answer_type, count in summary["answer_type_counts"].items():
        print(f"  {answer_type}: {count}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the simple SQL agent eval.")
    parser.add_argument(
        "--questions",
        default=DEFAULT_QUESTIONS_PATH,
        help="Path to eval questions JSON",
    )
    parser.add_argument(
        "--output",
        default=DEFAULT_OUTPUT_PATH,
        help="Path to write JSONL eval results",
    )
    parser.add_argument(
        "--db",
        default=DEFAULT_DB_PATH,
        help="Path to SQLite database",
    )
    args = parser.parse_args()

    summary = run_eval(
        questions_path=args.questions,
        output_path=args.output,
        db_path=args.db,
    )
    print_summary(summary)


if __name__ == "__main__":
    main()
