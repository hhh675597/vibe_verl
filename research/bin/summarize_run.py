#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

from _util import load_json, metric_better


INTERESTING_KEYS = [
    "training/global_step",
    "critic/rewards/mean",
    "response_length/mean",
    "response/aborted_ratio",
    "perf/time_per_step",
    "perf/throughput",
    "timing_s/step",
]


def choose_metric_key(metric_keys: set[str], preferred_exact: str | None) -> tuple[str | None, list[str]]:
    matched = sorted(metric_keys)
    if not matched:
        return None, matched
    if preferred_exact and preferred_exact in metric_keys:
        return preferred_exact, matched
    if len(matched) == 1:
        return matched[0], matched

    for marker in ("/acc/", "/reward/"):
        subset = [key for key in matched if marker in key]
        if len(subset) == 1:
            return subset[0], matched
    return matched[0], matched


def tail_lines(path: Path, limit: int = 100) -> list[str]:
    if not path.exists():
        return []
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    return lines[-limit:]


def extract_last_traceback(path: Path) -> str | None:
    """Pull the last Python traceback from a log file.

    Stops at the first exception line (the root cause), filtering out any
    noise that Ray or other frameworks print after the traceback.
    """
    if not path.exists():
        return None
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()

    # Strip ANSI escape codes for cleaner matching
    ansi_re = re.compile(r"\x1b\[[0-9;]*m")

    tb_start = None
    for i, line in enumerate(lines):
        if "Traceback (most recent call last):" in line:
            tb_start = i
    if tb_start is None:
        return None

    # Walk forward from the last Traceback header and stop after the
    # exception line (first non-indented, non-"File", non-blank line
    # after at least one "File" line).
    result: list[str] = []
    seen_file_line = False
    for line in lines[tb_start : tb_start + 200]:
        clean = ansi_re.sub("", line).strip()
        result.append(line)
        if clean.startswith("File "):
            seen_file_line = True
        elif seen_file_line and clean and not clean.startswith("File ") and not clean.startswith("Traceback"):
            # This is the exception line (e.g. "ValueError: ...")
            # Include one more: sometimes there's a chained "During handling..." block
            break

    return "\n".join(result)


def summarize_metrics(
    metrics_path: Path,
    primary_metric_key: str | None,
    primary_metric_pattern: str | None,
    primary_metric_mode: str,
) -> dict[str, Any]:
    metric_regex = re.compile(primary_metric_pattern) if primary_metric_pattern else None

    seen_keys: set[str] = set()
    primary_points: list[tuple[int, str, float]] = []
    last_values: dict[str, float] = {}
    total_records = 0
    last_step: int | None = None

    if not metrics_path.exists():
        return {
            "metrics_present": False,
            "matched_metric_keys": [],
            "primary_metric_key": None,
            "best_primary_metric": None,
            "best_primary_metric_step": None,
            "last_primary_metric": None,
            "total_metric_records": 0,
            "last_step": None,
            "interesting_last_values": {},
        }

    with metrics_path.open("r", encoding="utf-8") as f:
        for raw_line in f:
            line = raw_line.strip()
            if not line:
                continue
            total_records += 1
            record = json.loads(line)
            step = int(record.get("step", -1))
            data = record.get("data", {})
            last_step = step

            for key in INTERESTING_KEYS:
                value = data.get(key)
                if isinstance(value, (int, float)):
                    last_values[key] = float(value)

            for key, value in data.items():
                if not isinstance(value, (int, float)):
                    continue
                is_match = False
                if primary_metric_key and key == primary_metric_key:
                    is_match = True
                elif metric_regex and metric_regex.search(key):
                    is_match = True
                if is_match:
                    seen_keys.add(key)
                    primary_points.append((step, key, float(value)))

    chosen_key, matched_keys = choose_metric_key(seen_keys, primary_metric_key)
    chosen_points = [point for point in primary_points if point[1] == chosen_key] if chosen_key else []

    best_primary_metric = None
    best_primary_metric_step = None
    last_primary_metric = None

    if chosen_points:
        best_step, _, best_value = chosen_points[0]
        last_primary_metric = chosen_points[-1][2]
        for step, _, value in chosen_points[1:]:
            if metric_better(value, best_value, primary_metric_mode):
                best_step = step
                best_value = value
        best_primary_metric = best_value
        best_primary_metric_step = best_step

    return {
        "metrics_present": True,
        "matched_metric_keys": matched_keys,
        "primary_metric_key": chosen_key,
        "best_primary_metric": best_primary_metric,
        "best_primary_metric_step": best_primary_metric_step,
        "last_primary_metric": last_primary_metric,
        "total_metric_records": total_records,
        "last_step": last_step,
        "interesting_last_values": last_values,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Summarize a research harness run directory.")
    parser.add_argument("--run-dir", required=True, help="Run directory created by run_experiment.sh")
    parser.add_argument("--exit-code", required=True, type=int, help="Process exit code of the training run")
    parser.add_argument("--duration-sec", required=True, type=int, help="Wall clock duration in seconds")
    args = parser.parse_args()

    run_dir = Path(args.run_dir)
    manifest_path = run_dir / "manifest.json"
    driver_log_path = run_dir / "driver.log"
    metrics_path = run_dir / "metrics.jsonl"
    rollouts_dir = run_dir / "rollouts"
    validation_dir = run_dir / "validation"
    summary_path = run_dir / "summary.json"

    manifest = load_json(manifest_path)
    primary_metric_key = manifest.get("primary_metric_key") or None
    primary_metric_pattern = manifest.get("primary_metric_pattern") or None
    primary_metric_mode = manifest.get("primary_metric_mode", "max")

    metrics_summary = summarize_metrics(
        metrics_path=metrics_path,
        primary_metric_key=primary_metric_key,
        primary_metric_pattern=primary_metric_pattern,
        primary_metric_mode=primary_metric_mode,
    )

    if args.exit_code == 0:
        status = "success"
    elif args.exit_code == 124:
        status = "timeout"
    else:
        status = "failed"

    summary = {
        "run_id": manifest["run_id"],
        "recipe": manifest["recipe"],
        "profile": manifest["profile"],
        "idea_id": manifest["idea_id"],
        "seed": manifest["seed"],
        "status": status,
        "exit_code": args.exit_code,
        "duration_sec": args.duration_sec,
        "primary_metric_mode": primary_metric_mode,
        **metrics_summary,
        "rollout_files": len(list(rollouts_dir.glob("*.jsonl"))),
        "validation_files": len(list(validation_dir.glob("*.jsonl"))),
        "driver_log_tail": tail_lines(driver_log_path, limit=100),
        "error_traceback": extract_last_traceback(driver_log_path),
    }

    with summary_path.open("w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, sort_keys=True)
        f.write("\n")


if __name__ == "__main__":
    main()
