# vibe-verl — Agent-Driven Research Harness for VeRL

A thin experiment harness that lets a CLI agent (Claude Code, Codex, etc.) act as a
research assistant for LLM post-training experiments.
Built on top of [langfengQ/verl-agent](https://github.com/langfengQ/verl-agent)
(a fork of [VeRL](https://github.com/volcengine/verl) with agentic RL support).

Give the agent an idea — from a paper, a hypothesis, or a one-liner — and it drives
the full loop: **implement → debug → run → report**.

## Quick Start

**1. Set up your agent** — install [Claude Code](https://docs.anthropic.com/en/docs/claude-code),
[Codex](https://github.com/openai/codex), or any CLI agent that can read `AGENTS.md`.

**2. Configure the machine** — edit `research/env.sh` with machine-specific setup:

```bash
# research/env.sh (gitignored — safe for secrets)
ray stop --force >/dev/null 2>&1 || true
export CUDA_VISIBLE_DEVICES=0,1,2,3
export WANDB_API_KEY=your-key-here
```

**3. Write or adapt a recipe** — see `research/recipes/math_grpo_small/recipe.sh`.
A recipe defines the baseline command shape: model path, data files, GPU count, Hydra overrides.

> **Logger note:** `trainer.logger` must include `'file'` so that `metrics.jsonl` is written
> for the harness to consume. `console` is not recommended (noisy stdout).
> Wandb / TensorBoard / MLflow are optional alongside `file`.

**4. Give the agent an idea and let it work.** Expect light-to-moderate human-in-the-loop —
agents handle code changes and experiment iteration well, but may need help with
environment dependencies, GPU topology, or Ray cluster setup.

## Layout

```
research/
├── AGENTS.md                 # Agent playbook (the agent reads this)
├── env.sh                    # Machine-level setup: wandb API keys, CUDA, Ray, etc.
│
├── bin/                      # All scripts
│   ├── run_experiment.sh     # Main launcher (JSON stdout, always exits 0)
│   ├── init_idea.sh          # Scaffold a new idea workspace
│   ├── gen_report.py         # Generate report.md from run data
│   ├── summarize_run.py      # (internal) metrics.jsonl → summary.json
│   ├── append_ledger.py      # (internal) update ledger + best.json
│   └── _util.py              # (internal) shared Python helpers
│
├── recipes/<recipe>/         # Experiment configurations
│   ├── recipe.sh             #   Base Hydra overrides, model, data paths
│   ├── smoke.sh              #   Fast validation profile (2 steps)
│   └── full.sh               #   Real experiment profile (50+ steps)
│
├── ideas/<idea_id>/          # One directory per research idea
│   ├── spec.md               #   Hypothesis, plan, code changes, lab notebook
│   ├── overrides.txt         #   Hydra overrides for this idea (one per line)
│   ├── .runs                 #   Auto-maintained list of run_ids
│   └── report.md             #   Auto-generated report skeleton
│
├── runs/<run_id>/            # Per-run artifacts (gitignored)
│   ├── command.sh            #   Exact command that was launched
│   ├── manifest.json         #   Full config snapshot
│   ├── driver.log            #   Training stdout + stderr
│   ├── metrics.jsonl         #   Structured metrics (line-delimited JSON)
│   ├── summary.json          #   Post-run summary with status + metrics
│   ├── harness.log           #   Harness helper stderr
│   ├── env/                  #   Reproducibility snapshot (git state, nvidia-smi)
│   ├── rollouts/             #   Dumped rollout samples
│   ├── validation/           #   Dumped validation samples
│   ├── checkpoints/          #   Model checkpoints
│   └── hydra/                #   Hydra output dir
│
└── ledger/                   # Global experiment history 
    ├── runs.jsonl            #   Append-only: one row per run
    └── best.json             #   Per-recipe best successful run
```

## How It Works

### The agent's workflow

```
Phase 1   Understand the idea (read paper / user request)
Phase 2   bash research/bin/init_idea.sh <id>        → creates spec.md + overrides.txt
Phase 3   Edit VeRL source and/or overrides.txt
Phase 4   bash research/bin/run_experiment.sh ... --profile smoke
          Parse JSON output → diagnose → fix → retry
Phase 5   bash research/bin/run_experiment.sh ... --profile full
          Monitor metrics.jsonl during training
Phase 6   python research/bin/gen_report.py --idea <dir>
          Fill in conclusion
```

The agent operates with just **3 commands**. Everything else is automatic.

### What happens inside `run_experiment.sh`

```
run_experiment.sh
 ├─ Snapshot git state, env vars, nvidia-smi       → runs/<id>/env/
 ├─ Build command.sh from 5 override layers        → runs/<id>/command.sh
 ├─ Execute command.sh, capture output              → runs/<id>/driver.log
 ├─ summarize_run.py (auto)                         → runs/<id>/summary.json
 ├─ append_ledger.py (auto)                         → ledger/runs.jsonl + best.json
 └─ Print structured JSON result to stdout (for the agent to parse)
```

Exit code is always 0. Training success/failure is in `summary.json` and stdout.

### Override layering

The final Hydra command is built by concatenating five layers. Hydra uses
**last-one-wins** semantics — later layers override earlier ones.

```
 Priority   Source               Who edits        Example
 ────────   ──────               ─────────        ───────
 1 (low)    recipe.sh            Recipe author    algorithm.adv_estimator=grpo
 2          smoke.sh / full.sh   Recipe author    trainer.total_training_steps=2
 3          overrides.txt        Agent            algorithm.adv_estimator=maxrl
 4          --override CLI       Agent (ad-hoc)   data.train_batch_size=4
 5 (high)   MANDATORY            Harness (auto)   trainer.experiment_name=<run_id>
```

Machine-level setup (API keys, `CUDA_VISIBLE_DEVICES`, Ray teardown) goes in
`research/env.sh`, which is inlined into `command.sh` before the Python command.

## Example

See [`research/ideas/maxrl_2602_02710/`](research/ideas/maxrl_2602_02710/) for a
complete worked example: reproducing [MaxRL (arXiv:2602.02710)](https://arxiv.org/abs/2602.02710)
on the math environment(train: DAPO-math-17k, test: AIME24 avg@32) with DS-Distill-Qwen-1.5B on 8×H100.

- `spec.md` — full lab notebook with 22 log entries across 7 smoke retries and a successful full run of 50 steps
- `overrides.txt` — the Hydra overrides that differentiate MaxRL from the GRPO baseline
- `report.md` — auto-generated results with conclusion
