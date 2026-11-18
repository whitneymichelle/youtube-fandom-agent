"""
Run an eval question set against the deterministic SQL agent.
"""

from dataclasses import asdict
import argparse
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any, Dict, List
import webbrowser
from datetime import datetime, timezone
import uuid

from src.agents.simple_sql_agent import SimpleSQLAgent
from src.evaluation.export_review import export_review


DEFAULT_QUESTIONS_PATH = "evals/questions.json"
DEFAULT_OUTPUT_PATH = "evals/results/simple_sql_agent.jsonl"
DEFAULT_DB_PATH = "data/processed/youtube_fandom.db"
DEFAULT_HISTORY_PATH = "evals/history/runs.jsonl"


def load_questions(path: str) -> List[Dict[str, Any]]:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def write_jsonl(path: str, records: List[Dict[str, Any]]) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")


def build_human_review_status(
    question: Dict[str, Any],
    response_data: Dict[str, Any],
) -> Dict[str, Any]:
    reasons = []

    if question.get("requires_human_review", False):
        reasons.append(str(question.get("review_reason", "Pre-tagged for human review")))

    numeric_scores = [
        response_data[field]
        for field in (
            "groundedness",
            "interpretation_quality",
            "limitations_score",
            "overall_score",
        )
        if isinstance(response_data.get(field), (int, float))
    ]
    if numeric_scores and min(numeric_scores) < 3:
        reasons.append("LLM score below review threshold")

    comments_retrieved = response_data.get("comments_retrieved")
    comments_used = response_data.get("comments_used")
    if (
        isinstance(comments_retrieved, int)
        and comments_retrieved > 0
        and isinstance(comments_used, int)
        and comments_used == 0
    ):
        reasons.append("Comments retrieved but no comments used")

    if response_data.get("support_level") == "unsupported":
        reasons.append("Unsupported result")

    unique_reasons = list(dict.fromkeys(reasons))
    return {
        "needs_human_score": bool(unique_reasons),
        "human_review_reasons": unique_reasons,
    }


def capability_score(response_data: Dict[str, Any]) -> float:
    support_level = response_data.get("support_level")
    if support_level == "supported":
        return 5.0
    if support_level == "partially_supported":
        return 3.0
    return 0.0


def trial_consistency_score(trials: List[Dict[str, Any]]) -> float:
    if not trials:
        return 0.0
    signatures = []
    for trial in trials:
        signatures.append(
            json.dumps(
                {
                    "answer": trial.get("agent_answer"),
                    "sql": trial.get("sql"),
                    "rows": trial.get("rows"),
                    "support_level": trial.get("support_level"),
                },
                sort_keys=True,
                ensure_ascii=False,
            )
        )
    largest_group = max(signatures.count(signature) for signature in set(signatures))
    return round((largest_group / len(trials)) * 5, 2)


def run_eval(
    questions_path: str = DEFAULT_QUESTIONS_PATH,
    output_path: str = DEFAULT_OUTPUT_PATH,
    db_path: str = DEFAULT_DB_PATH,
    trial_count: int = 1,
    history_path: str | None = None,
) -> Dict[str, Any]:
    if trial_count < 1:
        raise ValueError("trial_count must be at least 1")

    questions = load_questions(questions_path)
    agent = SimpleSQLAgent(db_path)
    results = []

    for question in questions:
        question_trial_count = question.get("trial_count", trial_count)
        if question_trial_count < 1:
            raise ValueError("question trial_count must be at least 1")

        trials = []
        for trial_number in range(1, question_trial_count + 1):
            response = agent.answer(question["question"])
            response_data = asdict(response)
            human_review_status = build_human_review_status(question, response_data)
            trial = {
                "trial_number": trial_number,
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
                "grading_method": question.get("grading_method", "deterministic"),
                "evidence_source": question.get("evidence_source", "database"),
                "rubric": question.get("rubric", []),
                "can_determine": question.get("can_determine", []),
                "cannot_determine": question.get("cannot_determine", []),
                "agent": "simple_sql_agent",
                "agent_answer": response_data["answer"],
                "sql": response_data["sql"],
                "rows": response_data["rows"],
                "support_level": response_data["support_level"],
                "self_check": response_data["self_check"],
                "limitations": response_data["limitations"],
                "needs_human_score": human_review_status["needs_human_score"],
                "human_review_reasons": human_review_status["human_review_reasons"],
            }
            trial["capability_score"] = capability_score(trial)
            trials.append(trial)

        average_score = round(
            sum(trial["capability_score"] for trial in trials) / len(trials),
            2,
        )
        consistency_score = trial_consistency_score(trials)

        first_trial = trials[0]
        results.append(
            {
                **first_trial,
                "trial_count": question_trial_count,
                "trials": trials,
                "average_score": average_score,
                "consistency_score": consistency_score,
                "overall_score": average_score,
            }
        )

    write_jsonl(output_path, results)
    summary = summarize_results(results, output_path)

    question_scores = []
    deterministic_scores = []
    llm_scores = []
    for result in results:
        score = result.get("overall_score", 0.0)
        question_scores.append(
            {
                "question_id": result["question_id"],
                "question": result["question"],
                "grading_method": result.get("grading_method", "deterministic"),
                "support_level": result["support_level"],
                "average_score": score,
                "consistency_score": result.get("consistency_score", 5.0),
                "overall_score": score,
                "needs_human_score": result["needs_human_score"],
            }
        )
        if result.get("grading_method") == "llm":
            llm_scores.append(score)
        else:
            deterministic_scores.append(score)

    questions_bytes = Path(questions_path).read_bytes()
    average = lambda values: round(sum(values) / len(values), 2) if values else None
    snapshot = {
        "run_id": str(uuid.uuid4()),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        **get_git_metadata(),
        "agent": "simple_sql_agent",
        "question_set_hash": hashlib.sha256(questions_bytes).hexdigest(),
        "question_count": len(results),
        "overall_score": average([q["overall_score"] for q in question_scores]),
        "deterministic_score": average(deterministic_scores),
        "llm_score": average(llm_scores),
        "unsupported_count": sum(r["support_level"] == "unsupported" for r in results),
        "human_review_count": summary["human_review_needed"],
        "questions": question_scores,
    }
    if history_path:
        append_history_snapshot(history_path, snapshot)
    return summary


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


def get_git_metadata() -> Dict[str, Any]:
    try:
        commit = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        status = subprocess.run(
            ["git", "status", "--porcelain"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        return {"git_commit": commit, "git_dirty": bool(status)}
    except (subprocess.SubprocessError, FileNotFoundError):
        return {"git_commit": None, "git_dirty": None}


def append_history_snapshot(history_path: str, snapshot: Dict[str, Any]) -> None:
    path = Path(history_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(snapshot, ensure_ascii=False) + "\n")


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
    parser.add_argument(
        "--trials",
        type=int,
        default=1,
        help="Default trial count for questions without an explicit trial_count.",
    )
    parser.add_argument(
        "--open-report",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Open the generated HTML review dashboard after the eval completes.",
    )
    parser.add_argument(
        "--history",
        default=DEFAULT_HISTORY_PATH,
        help="Append run snapshots to this JSONL history file.",
    )
    parser.add_argument(
        "--no-history",
        action="store_true",
        help="Run without appending a history snapshot.",
    )
    args = parser.parse_args()

    summary = run_eval(
        questions_path=args.questions,
        output_path=args.output,
        db_path=args.db,
        trial_count=args.trials,
        history_path=args.history if not args.no_history else None,
    )
    print_summary(summary)

    if args.open_report:
        review_path = str(Path(args.output).with_name("simple_sql_agent_review.html"))
        export_review(
            results_path=args.output,
            review_path=review_path,
            overwrite=True,
        )
        webbrowser.open(f"file://{Path(review_path).resolve()}")


if __name__ == "__main__":
    main()
