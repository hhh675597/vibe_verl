"""Shared helpers for research harness scripts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def metric_better(lhs: float, rhs: float, mode: str) -> bool:
    """Return True if *lhs* is better than *rhs* according to *mode*."""
    if mode == "min":
        return lhs < rhs
    return lhs > rhs


def fmt_metric(value: Any) -> str:
    """Format a metric value for display in reports."""
    if value is None:
        return "-"
    if isinstance(value, float):
        return f"{value:.4f}"
    return str(value)
