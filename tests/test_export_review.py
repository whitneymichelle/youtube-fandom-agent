import json

from src.evaluation.export_review import export_review


def write_jsonl(path, records):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(json.dumps(record) for record in records) + "\n",
        encoding="utf-8",
    )


def make_result(question_id, needs_human_score):
    return {
        "question_id": question_id,
        "question": f"Question {question_id}?",
        "difficulty": "easy",
        "answer_type": "exact",
        "requires_human_review": needs_human_score,
        "expected_tables": ["fact_videos"],
        "expected_metrics": ["video_count"],
        "expected_dimensions": [],
        "expected_limitation": None,
        "agent": "simple_sql_agent",
        "agent_answer": "Answer.",
        "sql": "SELECT COUNT(*) AS video_count FROM fact_videos",
        "rows": [{"video_count": 3}],
        "support_level": "supported",
        "self_check": "Supported.",
        "limitations": [],
        "needs_human_score": needs_human_score,
    }


def test_export_review_writes_markdown_template(tmp_path):
    results_path = tmp_path / "results.jsonl"
    review_path = tmp_path / "review.md"
    write_jsonl(
        results_path,
        [make_result("q001", False), make_result("q002", True)],
    )

    summary = export_review(str(results_path), str(review_path))
    review = review_path.read_text(encoding="utf-8")

    assert summary["total_results"] == 2
    assert summary["review_items"] == 2
    assert "## q001: Question q001?" in review
    assert "## q002: Question q002?" in review
    assert "- Correctness: " in review
    assert "- Groundedness: " in review
    assert "- Self-awareness: " in review
    assert "Follow-up artifact updates" in review


def test_export_review_can_filter_to_human_review_items(tmp_path):
    results_path = tmp_path / "results.jsonl"
    review_path = tmp_path / "review.md"
    write_jsonl(
        results_path,
        [make_result("q001", False), make_result("q002", True)],
    )

    summary = export_review(str(results_path), str(review_path), human_only=True)
    review = review_path.read_text(encoding="utf-8")

    assert summary["total_results"] == 2
    assert summary["review_items"] == 1
    assert summary["human_only"] is True
    assert "## q001: Question q001?" not in review
    assert "## q002: Question q002?" in review
