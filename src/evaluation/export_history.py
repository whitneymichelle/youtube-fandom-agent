"""Export append-only eval history into a visual HTML dashboard."""

import argparse
import html
import json
from pathlib import Path
from typing import Any, Dict, List


DEFAULT_HISTORY_PATH = "evals/history/runs.jsonl"
DEFAULT_HISTORY_REVIEW_PATH = "evals/reviews/eval_history.html"


def load_history(path: str) -> List[Dict[str, Any]]:
    return [
        json.loads(line)
        for line in Path(path).read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def svg_trend(runs: List[Dict[str, Any]]) -> str:
    if not runs:
        return '<p>No history runs yet.</p>'

    width, height = 760, 220
    left, right, top, bottom = 48, 18, 18, 38
    plot_width = width - left - right
    plot_height = height - top - bottom

    def points(field: str, color: str) -> str:
        values = [run.get(field) for run in runs]
        usable = [(index, value) for index, value in enumerate(values) if value is not None]
        if not usable:
            return ""
        x_step = plot_width / max(len(runs) - 1, 1)
        coords = " ".join(
            f"{left + index * x_step:.1f},{top + plot_height * (1 - value / 5):.1f}"
            for index, value in usable
        )
        circles = "".join(
            f'<circle cx="{left + index * x_step:.1f}" cy="{top + plot_height * (1 - value / 5):.1f}" r="4" fill="{color}" />'
            for index, value in usable
        )
        return f'<polyline points="{coords}" fill="none" stroke="{color}" stroke-width="3" />{circles}'

    labels = "".join(
        f'<text x="{left + index * (plot_width / max(len(runs) - 1, 1)):.1f}" y="{height - 10}" font-size="11" text-anchor="middle">{html.escape(str(index + 1))}</text>'
        for index in range(len(runs))
    )
    grid = "".join(
        f'<line x1="{left}" x2="{width - right}" y1="{top + plot_height * (1 - value / 5):.1f}" y2="{top + plot_height * (1 - value / 5):.1f}" stroke="#dde4ec" />'
        f'<text x="{left - 8}" y="{top + plot_height * (1 - value / 5) + 4:.1f}" font-size="11" text-anchor="end">{value}</text>'
        for value in (0, 1, 2, 3, 4, 5)
    )
    return f'''<svg viewBox="0 0 {width} {height}" role="img" aria-label="Evaluation score trend">
      {grid}{labels}
      {points('overall_score', '#2563eb')}{points('deterministic_score', '#16a34a')}{points('llm_score', '#9333ea')}
    </svg>'''


def score_color(score: float | None) -> str:
    if score is None:
        return "#e5e7eb"
    if score >= 4:
        return "#bbf7d0"
    if score >= 3:
        return "#fde68a"
    return "#fecaca"


def heatmap(runs: List[Dict[str, Any]]) -> str:
    question_ids = sorted({q["question_id"] for run in runs for q in run.get("questions", [])})
    if not question_ids:
        return '<p>No question history yet.</p>'

    header = "".join(f"<th>Run {index + 1}</th>" for index in range(len(runs)))
    rows = []
    for question_id in question_ids:
        question_name = next(
            (q["question"] for run in runs for q in run.get("questions", []) if q["question_id"] == question_id),
            question_id,
        )
        cells = []
        for run in runs:
            match = next((q for q in run.get("questions", []) if q["question_id"] == question_id), None)
            score = match.get("overall_score") if match else None
            label = "—" if score is None else f"{score:.1f}"
            cells.append(f'<td style="background:{score_color(score)};text-align:center">{label}</td>')
        rows.append(f"<tr><td><strong>{html.escape(question_id)}</strong><br><small>{html.escape(question_name)}</small></td>{''.join(cells)}</tr>")

    body = "".join(rows)
    return (
        '<div class="table-wrap"><table><thead><tr><th>Question</th>'
        f"{header}</tr></thead><tbody>{body}</tbody></table></div>"
    )


def regression_table(runs: List[Dict[str, Any]]) -> str:
    if len(runs) < 2:
        return '<p>Run the eval at least twice to compare runs.</p>'

    previous = runs[-2].get("questions", [])
    current = runs[-1].get("questions", [])
    previous_scores = {q["question_id"]: q.get("overall_score") for q in previous}
    changes = []
    for question in current:
        question_id = question["question_id"]
        before = previous_scores.get(question_id)
        after = question.get("overall_score")
        if before is None or after is None:
            continue
        delta = round(after - before, 2)
        state = "Improved" if delta > 0 else "Regressed" if delta < 0 else "Stable"
        changes.append((question_id, before, after, delta, state))

    changes.sort(key=lambda item: item[3])
    rows = "".join(
        f"<tr><td>{html.escape(question_id)}</td><td>{before:.1f}</td><td>{after:.1f}</td><td>{delta:+.1f}</td><td>{state}</td></tr>"
        for question_id, before, after, delta, state in changes
    )
    return f'<div class="table-wrap"><table><thead><tr><th>Question</th><th>Previous</th><th>Current</th><th>Change</th><th>Status</th></tr></thead><tbody>{rows}</tbody></table></div>'


def render_history(runs: List[Dict[str, Any]]) -> str:
    run_count = len(runs)
    latest = runs[-1] if runs else {}
    return f'''<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Evaluation History</title><style>
:body{{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}}
body{{margin:0;background:#f4f7fb;color:#17202e;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}}.container{{max-width:1180px;margin:auto;padding:32px 20px 70px}}.stats{{display:grid;grid-template-columns:repeat(4,1fr);gap:14px}}.panel,.stat{{background:white;border:1px solid #dde4ec;border-radius:14px;padding:18px;box-shadow:0 7px 18px rgba(15,23,42,.05)}}.stat{{text-align:left}}.label{{color:#66758a;font-size:12px;text-transform:uppercase;letter-spacing:.08em}}.value{{font-size:28px;font-weight:750}}.panel{{margin-top:18px}}.legend{{display:flex;gap:16px;margin-bottom:10px;color:#66758a}}svg{{width:100%;height:auto}}.table-wrap{{overflow-x:auto}}table{{width:100%;border-collapse:collapse;background:white}}th,td{{border:1px solid #dde4ec;padding:10px;text-align:left;vertical-align:top}}th{{background:#f8fafc}}small{{color:#66758a}}@media(max-width:760px){{.stats{{grid-template-columns:1fr 1fr}}}}
</style></head><body><div class="container">
<h1>Evaluation history</h1><p>Append-only snapshots of eval runs.</p>
<div class="stats">
<div class="stat"><div class="label">Runs</div><div class="value">{run_count}</div></div>
<div class="stat"><div class="label">Latest overall</div><div class="value">{latest.get('overall_score','—')}</div></div>
<div class="stat"><div class="label">Latest deterministic</div><div class="value">{latest.get('deterministic_score','—')}</div></div>
<div class="stat"><div class="label">Latest LLM</div><div class="value">{latest.get('llm_score','—')}</div></div>
</div>
<div class="panel"><h2>Score trend</h2><div class="legend"><span>■ Overall</span><span>■ Deterministic</span><span>■ LLM</span></div>{svg_trend(runs)}</div>
<div class="panel"><h2>Question heatmap</h2>{heatmap(runs)}</div>
<div class="panel"><h2>Latest change from previous run</h2>{regression_table(runs)}</div>
</div></body></html>'''


def export_history(history_path: str = DEFAULT_HISTORY_PATH, output_path: str = DEFAULT_HISTORY_REVIEW_PATH) -> Dict[str, Any]:
    runs = load_history(history_path)
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_history(runs), encoding="utf-8")
    return {"history_path": history_path, "output_path": output_path, "run_count": len(runs)}


def main() -> None:
    parser = argparse.ArgumentParser(description="Export eval history to an HTML dashboard.")
    parser.add_argument("--history", default=DEFAULT_HISTORY_PATH)
    parser.add_argument("--output", default=DEFAULT_HISTORY_REVIEW_PATH)
    args = parser.parse_args()
    export_history(args.history, args.output)


if __name__ == "__main__":
    main()
