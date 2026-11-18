import json

from src.evaluation.export_history import export_history, heatmap, regression_table


def write_runs(path, runs):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(run) for run in runs) + "\n", encoding="utf-8")


def make_run(run_id, scores):
    return {
        "run_id": run_id,
        "timestamp": "2026-11-17T00:00:00+00:00",
        "agent": "simple_sql_agent",
        "overall_score": sum(scores.values()) / len(scores),
        "deterministic_score": 4.0,
        "llm_score": 3.0,
        "questions": [
            {
                "question_id": question_id,
                "question": f"Question {question_id}",
                "grading_method": "deterministic",
                "support_level": "supported" if score >= 3 else "unsupported",
                "overall_score": score,
                "consistency_score": 5.0,
                "needs_human_score": False,
            }
            for question_id, score in scores.items()
        ],
    }


def test_export_history_writes_dashboard(tmp_path):
    history_path = tmp_path / "runs.jsonl"
    output_path = tmp_path / "history.html"
    write_runs(history_path, [make_run("run-1", {"q001": 5.0}), make_run("run-2", {"q001": 3.0})])

    summary = export_history(str(history_path), str(output_path))
    html = output_path.read_text(encoding="utf-8")

    assert summary["run_count"] == 2
    assert "Evaluation history" in html
    assert "Score trend" in html
    assert "Question heatmap" in html
    assert "Latest change" in html


def test_heatmap_and_regression_show_question_scores(tmp_path):
    runs = [make_run("run-1", {"q001": 5.0, "q002": 0.0}), make_run("run-2", {"q001": 3.0, "q002": 5.0})]

    heatmap_html = heatmap(runs)
    regression_html = regression_table(runs)

    assert "q001" in heatmap_html
    assert "q002" in heatmap_html
    assert "Regressed" in regression_html
    assert "Improved" in regression_html
