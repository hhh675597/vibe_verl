#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from _util import load_json, metric_better


def main() -> None:
    parser = argparse.ArgumentParser(description="Append a run summary to the research ledger.")
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--summary", required=True)
    parser.add_argument("--ledger", required=True)
    parser.add_argument("--best", required=True)
    args = parser.parse_args()

    manifest_path = Path(args.manifest)
    summary_path = Path(args.summary)
    ledger_path = Path(args.ledger)
    best_path = Path(args.best)

    manifest = load_json(manifest_path)
    summary = load_json(summary_path)

    ledger_path.parent.mkdir(parents=True, exist_ok=True)
    best_path.parent.mkdir(parents=True, exist_ok=True)

    row = {
        "run_id": manifest["run_id"],
        "recipe": manifest["recipe"],
        "profile": manifest["profile"],
        "idea_id": manifest["idea_id"],
        "seed": manifest["seed"],
        "note": manifest.get("note", ""),
        "entrypoint": manifest["entrypoint"],
        "project_name": manifest["project_name"],
        "primary_metric_mode": manifest["primary_metric_mode"],
        "primary_metric_key": summary.get("primary_metric_key"),
        "status": summary["status"],
        "exit_code": summary["exit_code"],
        "duration_sec": summary["duration_sec"],
        "best_primary_metric": summary.get("best_primary_metric"),
        "last_primary_metric": summary.get("last_primary_metric"),
        "best_primary_metric_step": summary.get("best_primary_metric_step"),
        "last_step": summary.get("last_step"),
        "metrics_path": manifest["artifacts"]["metrics"],
        "driver_log_path": manifest["artifacts"]["driver_log"],
        "rollout_dir": manifest["artifacts"]["rollouts"],
        "validation_dir": manifest["artifacts"]["validation"],
        "checkpoint_dir": manifest["artifacts"]["checkpoints"],
        "summary_path": str(summary_path),
        "manifest_path": str(manifest_path),
    }

    with ledger_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False))
        f.write("\n")

    if best_path.exists():
        best = load_json(best_path)
    else:
        best = {}

    recipe = manifest["recipe"]
    mode = manifest["primary_metric_mode"]
    candidate_metric = summary.get("best_primary_metric")
    current = best.get(recipe)

    if summary["status"] == "success" and isinstance(candidate_metric, (int, float)):
        should_update = current is None
        if current is not None:
            current_metric = current.get("best_primary_metric")
            should_update = current_metric is None or metric_better(candidate_metric, current_metric, mode)
        if should_update:
            best[recipe] = {
                "run_id": manifest["run_id"],
                "profile": manifest["profile"],
                "idea_id": manifest["idea_id"],
                "seed": manifest["seed"],
                "primary_metric_mode": mode,
                "primary_metric_key": summary.get("primary_metric_key"),
                "best_primary_metric": candidate_metric,
                "best_primary_metric_step": summary.get("best_primary_metric_step"),
                "summary_path": str(summary_path),
            }

    with best_path.open("w", encoding="utf-8") as f:
        json.dump(best, f, indent=2, sort_keys=True)
        f.write("\n")


if __name__ == "__main__":
    main()
