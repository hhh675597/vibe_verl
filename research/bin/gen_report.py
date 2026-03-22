#!/usr/bin/env python3
"""Generate a report skeleton for an idea from its run data.

Usage:
    python research/bin/gen_report.py --idea research/ideas/<id>

Reads:
    - <idea_dir>/.runs                  run ids
    - research/runs/<run_id>/summary.json
    - research/ledger/best.json         current baseline (if available)

Writes:
    - <idea_dir>/report.md              report skeleton
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any

from _util import fmt_metric, load_json, metric_better


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a report for an idea.")
    parser.add_argument("--idea", required=True, help="Idea directory path")
    args = parser.parse_args()

    idea_dir = Path(args.idea).resolve()
    idea_id = idea_dir.name
    research_root = idea_dir.parent.parent
    runs_root = research_root / "runs"

    # ── Load run data ──────────────────────────────────────────────
    runs_file = idea_dir / ".runs"
    run_ids: list[str] = []
    if runs_file.exists():
        run_ids = [
            line.strip()
            for line in runs_file.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]

    summaries: list[dict[str, Any]] = []
    for run_id in run_ids:
        summary_path = runs_root / run_id / "summary.json"
        if summary_path.exists():
            summaries.append(load_json(summary_path))

    # ── Load baseline from ledger ─────────────────────────────────
    best_path = research_root / "ledger" / "best.json"
    baseline: dict[str, Any] | None = None
    if best_path.exists():
        best_data = load_json(best_path)
        # Find the recipe from the first summary that has one
        recipe = None
        for s in summaries:
            recipe = s.get("recipe")
            if recipe:
                break
        if recipe:
            baseline = best_data.get(recipe)

    # ── Read spec.md first line for title ──────────────────────────
    spec_path = idea_dir / "spec.md"
    title = idea_id
    if spec_path.exists():
        first_line = spec_path.read_text(encoding="utf-8").split("\n", 1)[0].strip()
        if first_line.startswith("# "):
            title = first_line[2:].strip()

    # ── Build report ───────────────────────────────────────────────
    lines: list[str] = []
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    lines.append(f"# Report: {title}")
    lines.append("")
    lines.append(f"*Generated: {timestamp} | idea_id: `{idea_id}`*")
    lines.append("")

    # ── Find best successful run from this idea ────────────────────
    successful = [
        s for s in summaries
        if s.get("status") == "success" and isinstance(s.get("best_primary_metric"), (int, float))
    ]
    mode = summaries[0].get("primary_metric_mode", "max") if summaries else "max"

    best_run: dict[str, Any] | None = None
    if successful:
        best_run = successful[0]
        for s in successful[1:]:
            if metric_better(s["best_primary_metric"], best_run["best_primary_metric"], mode):
                best_run = s

    # Status badge
    if best_run and baseline and isinstance(baseline.get("best_primary_metric"), (int, float)):
        improved = metric_better(best_run["best_primary_metric"], baseline["best_primary_metric"], mode)
        if improved:
            lines.append("## Status: Improved over baseline")
        else:
            lines.append("## Status: No improvement over baseline")
    elif best_run:
        lines.append("## Status: No baseline available for comparison")
    else:
        lines.append("## Status: No successful runs")
    lines.append("")

    # Results table
    if best_run and baseline and isinstance(baseline.get("best_primary_metric"), (int, float)):
        metric_key = best_run.get("primary_metric_key", "primary metric")
        base_val = baseline["best_primary_metric"]
        cand_val = best_run["best_primary_metric"]
        delta = cand_val - base_val
        delta_pct = (delta / abs(base_val) * 100) if base_val != 0 else None

        lines.append("## Results")
        lines.append("")
        lines.append(f"| `{metric_key}` | Baseline | {idea_id} | Delta | Delta% |")
        lines.append("|---|---------|-----------|-------|--------|")
        lines.append(
            f"| value | {fmt_metric(base_val)} "
            f"| {fmt_metric(cand_val)} "
            f"| {fmt_metric(round(delta, 6))} "
            f"| {fmt_metric(round(delta_pct, 2) if delta_pct is not None else None)}% |"
        )
        lines.append(
            f"| best step | {fmt_metric(baseline.get('best_primary_metric_step'))} "
            f"| {fmt_metric(best_run.get('best_primary_metric_step'))} | | |"
        )
        lines.append(
            f"| duration (s) | - "
            f"| {fmt_metric(best_run.get('duration_sec'))} | | |"
        )
        lines.append("")
    elif best_run:
        lines.append("## Results")
        lines.append("")
        lines.append(f"*No baseline available for comparison.*")
        lines.append("")
        lines.append(f"- **Best metric**: {fmt_metric(best_run.get('best_primary_metric'))}")
        lines.append(f"- **Best step**: {fmt_metric(best_run.get('best_primary_metric_step'))}")
        lines.append(f"- **Duration**: {fmt_metric(best_run.get('duration_sec'))}s")
        lines.append("")

    # Run history table
    if summaries:
        lines.append("## Run History")
        lines.append("")
        lines.append("| Run ID | Profile | Status | Best Metric | Steps | Duration |")
        lines.append("|--------|---------|--------|-------------|-------|----------|")
        for s in summaries:
            run_id_short = s["run_id"][:40] + "..." if len(s["run_id"]) > 40 else s["run_id"]
            lines.append(
                f"| {run_id_short} "
                f"| {s.get('profile', '-')} "
                f"| {s.get('status', '-')} "
                f"| {fmt_metric(s.get('best_primary_metric'))} "
                f"| {fmt_metric(s.get('last_step'))} "
                f"| {fmt_metric(s.get('duration_sec'))}s |"
            )
        lines.append("")

    # Error summary (if any failed runs)
    failed = [s for s in summaries if s.get("status") in ("failed", "timeout")]
    if failed:
        lines.append("## Errors Encountered")
        lines.append("")
        for s in failed:
            lines.append(f"### {s['run_id']}")
            lines.append(f"- **Status**: {s.get('status')} (exit code {s.get('exit_code')})")
            tb = s.get("error_traceback")
            if tb:
                lines.append(f"- **Traceback**:")
                lines.append("```")
                # Limit traceback to 30 lines in report
                tb_lines = tb.split("\n")
                if len(tb_lines) > 30:
                    lines.extend(tb_lines[:10])
                    lines.append(f"  ... ({len(tb_lines) - 20} lines omitted) ...")
                    lines.extend(tb_lines[-10:])
                else:
                    lines.extend(tb_lines)
                lines.append("```")
            else:
                tail = s.get("driver_log_tail", [])
                if tail:
                    lines.append(f"- **Log tail** (last {len(tail)} lines):")
                    lines.append("```")
                    lines.extend(tail[-15:])
                    lines.append("```")
            lines.append("")

    # Conclusion placeholder
    lines.append("## Conclusion")
    lines.append("")
    lines.append("<!-- Fill in your interpretation of the results. -->")
    lines.append("")

    # ── Write ──────────────────────────────────────────────────────
    report_path = idea_dir / "report.md"
    report_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"report written: {report_path}")


if __name__ == "__main__":
    main()
