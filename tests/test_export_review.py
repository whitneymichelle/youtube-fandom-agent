import json

import pytest

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


def test_export_review_writes_html_dashboard(tmp_path):
    results_path = tmp_path / "results.jsonl"
    review_path = tmp_path / "review.html"
    write_jsonl(
        results_path,
        [make_result("q001", False), make_result("q002", True)],
    )

    summary = export_review(str(results_path), str(review_path))
    review = review_path.read_text(encoding="utf-8")

    assert summary["total_results"] == 2
    assert summary["review_items"] == 2
    assert "<title>Simple SQL Agent Review</title>" in review
    assert "<h2>Summary</h2>" in review
    assert "Total eval questions" in review
    assert "q001" in review
    assert "q002" in review
    assert "Agent answer" in review
    assert "Self-check" in review
    assert "Review weak cases" in review


def test_export_review_can_filter_to_human_review_items(tmp_path):
    results_path = tmp_path / "results.jsonl"
    review_path = tmp_path / "review.html"
    write_jsonl(
        results_path,
        [make_result("q001", False), make_result("q002", True)],
    )

    summary = export_review(str(results_path), str(review_path), human_only=True)
    review = review_path.read_text(encoding="utf-8")

    assert summary["total_results"] == 2
    assert summary["review_items"] == 1
    assert summary["human_only"] is True
    assert "q002" in review
    assert "q001" not in review


def test_export_review_refuses_to_overwrite_existing_review(tmp_path):
    results_path = tmp_path / "results.jsonl"
    review_path = tmp_path / "review.html"
    write_jsonl(results_path, [make_result("q001", True)])
    review_path.write_text("human notes\n", encoding="utf-8")

    with pytest.raises(FileExistsError, match="Use --overwrite"):
        export_review(str(results_path), str(review_path))

    assert review_path.read_text(encoding="utf-8") == "human notes\n"


def test_export_review_can_overwrite_existing_review_when_requested(tmp_path):
    results_path = tmp_path / "results.jsonl"
    review_path = tmp_path / "review.html"
    write_jsonl(results_path, [make_result("q001", True)])
    review_path.write_text("old review\n", encoding="utf-8")

    summary = export_review(str(results_path), str(review_path), overwrite=True)
    review = review_path.read_text(encoding="utf-8")

    assert summary["overwrite"] is True
    assert "old review" not in review
    assert "q001" in review


def test_export_review_renders_llm_comment_evidence(tmp_path):
    results_path = tmp_path / "results.jsonl"
    review_path = tmp_path / "review.html"
    result = make_result("q015", True)
    result.update(
        {
            "grading_method": "llm",
            "evidence_source": "comments",
            "rubric": ["groundedness", "interpretation_quality", "limitations"],
            "comments_retrieved": 482,
            "comments_used": 75,
            "sample_comment_ids": ["c123", "c441", "c620"],
            "groundedness": 4,
            "interpretation_quality": 3,
            "limitations_score": 5,
            "overall_score": 4.0,
            "judge_reasoning": "Themes are supported, but one audience-wide conclusion is overstated.",
            "can_determine": ["recurring themes across retrieved comments"],
            "cannot_determine": ["fandom-wide sentiment", "whether commenters represent all viewers"],
        }
    )
    write_jsonl(results_path, [result])

    export_review(str(results_path), str(review_path), overwrite=True)
    review = review_path.read_text(encoding="utf-8")

    assert "LLM grading" in review
    assert "482" in review
    assert "75" in review
    assert "4/5" in review
    assert "Judge reasoning" in review
    assert "What can be determined" in review
    assert "What cannot be determined" in review
    assert "fandom-wide sentiment" in review
