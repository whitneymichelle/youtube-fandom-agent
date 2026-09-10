import json

from src.evaluation.run_eval import run_eval
from tests.test_simple_sql_agent import create_agent_db


def test_run_eval_writes_jsonl_results_and_summary(tmp_path):
    db_path = create_agent_db(tmp_path)
    questions_path = tmp_path / "questions.json"
    output_path = tmp_path / "results.jsonl"
    questions = [
        {
            "id": "q001",
            "question": "How many videos are in the dataset?",
            "difficulty": "easy",
            "answer_type": "exact",
            "expected_tables": ["fact_videos"],
            "expected_metrics": ["video_count"],
            "requires_human_review": False,
        },
        {
            "id": "q002",
            "question": "Can we tell what fans are saying in the comments?",
            "difficulty": "hard",
            "answer_type": "answerability",
            "expected_tables": ["fact_videos"],
            "expected_metrics": ["comment_count"],
            "requires_human_review": True,
        },
    ]
    questions_path.write_text(json.dumps(questions), encoding="utf-8")

    summary = run_eval(
        questions_path=str(questions_path),
        output_path=str(output_path),
        db_path=str(db_path),
    )

    result_rows = [
        json.loads(line)
        for line in output_path.read_text(encoding="utf-8").splitlines()
    ]

    assert summary["total_questions"] == 2
    assert summary["answered_with_sql"] == 1
    assert summary["answered_without_sql"] == 1
    assert summary["human_review_needed"] == 1
    assert summary["support_counts"] == {"supported": 1, "unsupported": 1}
    assert result_rows[0]["question_id"] == "q001"
    assert result_rows[0]["agent"] == "simple_sql_agent"
    assert result_rows[0]["support_level"] == "supported"
    assert result_rows[0]["sql"] == "SELECT COUNT(*) AS video_count FROM fact_videos"
    assert result_rows[0]["rows"] == [{"video_count": 3}]
    assert result_rows[1]["question_id"] == "q002"
    assert result_rows[1]["support_level"] == "unsupported"
    assert result_rows[1]["needs_human_score"] is True
