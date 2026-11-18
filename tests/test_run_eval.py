import json
import sys

import src.evaluation.run_eval as eval_module
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


def test_human_review_status_combines_static_and_dynamic_triggers():
    question = {
        "requires_human_review": True,
        "review_reason": "Comment interpretation is subjective",
    }
    response = {
        "support_level": "unsupported",
        "groundedness": 2,
        "comments_retrieved": 482,
        "comments_used": 0,
    }

    status = eval_module.build_human_review_status(question, response)

    assert status["needs_human_score"] is True
    assert "Comment interpretation is subjective" in status["human_review_reasons"]
    assert "LLM score below review threshold" in status["human_review_reasons"]
    assert "Comments retrieved but no comments used" in status["human_review_reasons"]
    assert "Unsupported result" in status["human_review_reasons"]


def test_main_only_opens_report_when_requested(monkeypatch):
    calls = {"export": 0, "browser": 0}

    monkeypatch.setattr(eval_module, "run_eval", lambda **kwargs: {"output_path": "evals/results/test.jsonl"})
    monkeypatch.setattr(eval_module, "print_summary", lambda summary: None)
    monkeypatch.setattr(eval_module, "export_review", lambda **kwargs: calls.__setitem__("export", calls["export"] + 1))
    monkeypatch.setattr(eval_module.webbrowser, "open", lambda *args, **kwargs: calls.__setitem__("browser", calls["browser"] + 1))

    monkeypatch.setattr(sys, "argv", ["run_eval"])
    eval_module.main()
    assert calls == {"export": 0, "browser": 0}

    monkeypatch.setattr(sys, "argv", ["run_eval", "--open-report"])
    eval_module.main()
    assert calls == {"export": 1, "browser": 1}


def test_default_eval_questions_are_realistic_and_regression_safe():
    with open("evals/questions.json", encoding="utf-8") as f:
        questions = json.load(f)

    assert len(questions) >= 12
    assert {q["answer_type"] for q in questions} >= {"exact", "grouped", "comparison"}
    assert any("what" in q["question"].lower() for q in questions)
    assert any("which" in q["question"].lower() for q in questions)
    assert any("do " in q["question"].lower() for q in questions)


def test_run_eval_records_three_trials_and_numeric_score(tmp_path):
    db_path = create_agent_db(tmp_path)
    questions_path = tmp_path / "questions.json"
    output_path = tmp_path / "results.jsonl"
    questions = [
        {
            "id": "q002",
            "question": "Can we tell what fans are saying in the comments?",
            "difficulty": "hard",
            "answer_type": "answerability",
            "requires_human_review": True,
        }
    ]
    questions_path.write_text(json.dumps(questions), encoding="utf-8")

    run_eval(
        questions_path=str(questions_path),
        output_path=str(output_path),
        db_path=str(db_path),
        trial_count=3,
    )

    result = json.loads(output_path.read_text(encoding="utf-8").strip())
    assert result["trial_count"] == 3
    assert len(result["trials"]) == 3
    assert result["average_score"] == 0.0
    assert result["consistency_score"] == 5
    assert result["overall_score"] == 0.0
