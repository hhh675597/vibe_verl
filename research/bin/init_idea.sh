#!/usr/bin/env bash
# Create a new idea workspace under research/ideas/<idea_id>/
set -euo pipefail

die() { echo "error: $*" >&2; exit 1; }

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RESEARCH_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
IDEAS_ROOT="${RESEARCH_ROOT}/ideas"

IDEA_ID="${1:-}"
[[ -n "$IDEA_ID" ]] || die "usage: bash research/bin/init_idea.sh <idea_id>"

# Sanitize: lowercase, replace non-alnum with dash
IDEA_ID="$(echo "$IDEA_ID" | tr '[:upper:]' '[:lower:]' | sed -E 's/[^a-z0-9._-]+/-/g; s/^-+//; s/-+$//')"

IDEA_DIR="${IDEAS_ROOT}/${IDEA_ID}"
[[ ! -d "$IDEA_DIR" ]] || die "idea already exists: $IDEA_DIR"

mkdir -p "$IDEA_DIR"

# ── spec.md template ──────────────────────────────────────────────
cat > "${IDEA_DIR}/spec.md" <<'SPEC'
# <TITLE>

## Source
<!-- Paper URL / section, or user request that motivated this idea -->

## Hypothesis
<!-- What do you expect to happen and why? -->

## Plan
- [ ] Understand the idea
- [ ] Implement (code changes and/or config overrides)
- [ ] Smoke test
- [ ] Full run
- [ ] Write report

## Code Changes
<!-- List every modified file and summarise what was changed.
     Example:
     ### verl/trainer/ppo/core_algos.py
     - Added `compute_clipped_kl()` (lines 145-162)
     - Modified `compute_policy_loss()` to call it
-->

## Log
<!-- Chronological lab notebook: what you tried, what happened.
     Example:
     - 2025-03-20 14:30  Smoke run failed (OOM). Reduced micro_batch to 1.
     - 2025-03-20 14:45  Smoke passed. reward looks reasonable.
-->
SPEC

# ── overrides.txt (one Hydra override per line) ─────────────────
cat > "${IDEA_DIR}/overrides.txt" <<'OVER'
# Hydra config overrides for this idea — one per line.
# Delete this file if the idea is code-only and needs no config changes.
# Example:
#   actor_rollout_ref.actor.optim.lr=5e-6
OVER

echo "idea created: ${IDEA_DIR}"
echo "  → edit spec.md to describe your hypothesis and plan"
echo "  → edit overrides.txt to add Hydra overrides (or delete it if code-only)"
