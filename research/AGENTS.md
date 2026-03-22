# Research Assistant Workflow

You are a research assistant for LLM RL post-training experiments using **VeRL** (a Ray-based post-training infrastructure). Your job is to take a research idea — from a paper, a user prompt, or your own hypothesis — and drive it through implementation, experimentation, debugging, and reporting.

## End-to-End Workflow

### Phase 1 — Understand the Idea
- Read the paper / user description carefully.
- Identify: what is the hypothesis? What changes are needed (code, config, or both)?
- Ask clarifying questions if the scope is ambiguous.

### Phase 2 — Create Idea Workspace
```bash
bash research/bin/init_idea.sh <idea_id>
```
This creates `research/ideas/<idea_id>/` with a `spec.md` template and empty `overrides.txt`.

Fill in `spec.md`:
- **Source**: paper link, section, equation numbers, or user request.
- **Hypothesis**: what you expect and why.
- **Plan**: checklist of implementation steps.
- Update Plan checkboxes as you progress.

### Phase 3 — Implement
- **Config-only idea?** → edit `overrides.txt` with Hydra overrides (one per line).
- **Code change needed?** → modify VeRL source files directly. Document every changed file under `## Code Changes` in `spec.md`.
- **Both?** → do both.
- When done, check off the implement step in `spec.md`.

### Phase 4 — Smoke Test
```bash
bash research/bin/run_experiment.sh \
    --recipe <RECIPE> --profile smoke \
    --idea research/ideas/<idea_id>
```
- The launcher prints JSON to stdout. Parse the last line (`event: "done"`) for `status`, `error_traceback`, and `run_dir`.
- If **failed**: read `driver_log_tail` from the JSON output (last ~30 lines of training output). If insufficient, read `<run_dir>/driver.log` for the full raw output. Log what happened in `spec.md` → `## Log`. Then diagnose, fix, and re-run smoke.
- If **success**: proceed to full run.
- **After every smoke attempt** (pass or fail): update `spec.md` — check off the step if passed, and always add a timestamped entry to `## Log` describing the outcome.

### Phase 5 — Full Run
```bash
bash research/bin/run_experiment.sh \
    --recipe <RECIPE> --profile full \
    --idea research/ideas/<idea_id>
```
- **After the run**: update `spec.md` — check off the step, add a `## Log` entry with the result (metric value, duration, or failure reason).

### Phase 6 — Report
```bash
python research/bin/gen_report.py \
    --idea research/ideas/<idea_id>
```
- `gen_report.py` generates a `report.md` skeleton with results table, run history, and error summary.
- Review the generated report, fill in `## Conclusion`.
- To judge improvement: read `summary.json` for your run and `research/ledger/best.json` for the current baseline.
- Update `spec.md`: check off remaining Plan items, add final Log entry.

---

## Worked Example

**User says**: "Read arXiv:2602.12345 — they propose a clipped KL estimator. Implement it and see if it helps on GSM8K GRPO."

```
# Phase 1: Understand
→ WebFetch the paper, read Section 3.2, extract Equation (7).

# Phase 2: Create workspace
bash research/bin/init_idea.sh clipped-kl
→ Edit research/ideas/clipped-kl/spec.md:
    Source: arXiv:2602.12345, Section 3.2, Eq. (7)
    Hypothesis: Clipped KL allows 10x higher coef without instability.
    Plan:
      - [x] Read paper
      - [ ] Add compute_clipped_kl() in core_algos.py
      - [ ] Set kl_coef=0.01 in overrides.txt
      - [ ] Smoke test
      - [ ] Full run
      - [ ] Report

# Phase 3: Implement
→ Edit verl/trainer/ppo/core_algos.py: add compute_clipped_kl()
→ Edit overrides.txt: actor_rollout_ref.actor.optim.lr=5e-6
                       algorithm.kl_ctrl.kl_coef=0.01
→ Update spec.md Plan checkboxes

# Phase 4: Smoke test
bash research/bin/run_experiment.sh \
    --recipe math_grpo_small --profile smoke \
    --idea research/ideas/clipped-kl
→ Parse JSON output → status: "failed", error_traceback shows NameError
→ Fix the typo, log it in spec.md
→ Re-run smoke → success

# Phase 5: Full run
bash research/bin/run_experiment.sh \
    --recipe math_grpo_small --profile full \
    --idea research/ideas/clipped-kl

# Phase 6: Report
python research/bin/gen_report.py --idea research/ideas/clipped-kl
→ Read summary.json + ledger/best.json to judge improvement
→ Edit report.md, add conclusion:
    "Clipped KL with coef=0.01 improved val reward by 15.6%.
     Recommend adopting as new baseline."
```

---

## Directory Structure

```
research/
├── AGENTS.md                     # This file
├── env.sh                        # Machine-level env setup (gitignored)
├── bin/
│   ├── run_experiment.sh         # Main experiment launcher
│   ├── init_idea.sh              # Scaffold a new idea workspace
│   ├── _util.py                  # Shared Python helpers
│   ├── summarize_run.py          # Post-run: metrics.jsonl → summary.json
│   ├── append_ledger.py          # Post-run: update ledger + best.json
│   └── gen_report.py             # Generate report.md from run data
├── ideas/                        # One subdirectory per idea
│   └── <idea_id>/
│       ├── spec.md               # Hypothesis, plan, code changes, log
│       ├── overrides.txt          # Optional: Hydra config overrides (one per line)
│       ├── .runs                 # Auto-maintained: list of run_ids
│       └── report.md             # Auto-generated skeleton, agent fills conclusion
├── recipes/                      # Experiment configurations
│   └── <recipe_name>/
│       ├── recipe.sh             # Base Hydra overrides + defaults
│       ├── smoke.sh              # Fast validation profile (2 steps)
│       └── full.sh               # Real experiment profile (50 steps)
├── runs/                         # One subdirectory per run (gitignored)
│   └── <run_id>/
│       ├── manifest.json         # Full config snapshot
│       ├── command.sh            # Exact command that was launched
│       ├── driver.log            # Full stdout+stderr
│       ├── metrics.jsonl         # Structured metrics (line-delimited JSON)
│       ├── summary.json          # Post-run summary with metrics + errors
│       ├── env/                  # Reproducibility: git state, nvidia-smi, etc.
│       ├── rollouts/
│       ├── validation/
│       ├── checkpoints/
│       └── hydra/
└── ledger/                       # Global experiment history (gitignored)
    ├── runs.jsonl                # Append-only: one row per run
    └── best.json                 # Per-recipe best successful run
```

---

## Debugging a Failed Run

### Quick Diagnosis
1. Parse the JSON `"done"` line printed to stdout:
   - `status`: "failed", "timeout", or "success"
   - `driver_log_tail`: last ~30 lines of training output (only present for failed/timeout runs)
   - `run_id` and other key metrics
2. If the tail is insufficient, read `<run_dir>/driver.log` directly.

### Decision Tree

```
smoke failed?
├── error_traceback contains "OutOfMemoryError" or "CUDA out of memory"
│   → Reduce batch size:
│     --override data.train_batch_size=1
│     --override actor_rollout_ref.actor.ppo_micro_batch_size_per_gpu=1
│
├── exit_code == 124 (timeout)
│   → Increase timeout or reduce steps:
│     --override trainer.total_training_steps=1
│
├── error_traceback contains "HydraException" or "ConfigAttributeError"
│   → Fix override syntax: check key names, quoting, typos
│   → Tip: use --dry-run to validate without launching training
│
├── error_traceback contains "CUDA error" or "NCCL"
│   → Check GPU state: nvidia-smi
│   → May need to restart Ray: ray stop && ray start --head
│
├── error_traceback contains "ImportError" or "ModuleNotFoundError"
│   → Missing dependency or broken import path
│
├── error_traceback contains "KeyError" / "AttributeError" in VeRL code
│   → Your code change likely has a bug. Read the traceback carefully.
│
└── No traceback, just hangs and times out
    → Likely a Ray actor deadlock. Check if all GPUs are visible.
    → Try reducing n_gpus_per_node or rollout tensor_parallel_size.
```

### Always Log Your Debugging
After every failed attempt, add an entry to `spec.md` → `## Log`:
```markdown
- 2025-03-20 14:30  Smoke failed (OOM). Reduced micro_batch from 2 to 1.
- 2025-03-20 14:45  Smoke failed (Hydra error). Fixed typo: kl_coeff → kl_coef.
- 2025-03-20 15:00  Smoke passed. reward=0.38, looks reasonable.
```

---

## VeRL Code Map — Where to Make Changes

| What you want to change | File |
|--------------------------|------|
| Reward / scoring functions | `verl/utils/reward_score/...` |
| Loss computation (PPO, KL, etc.) | `verl/trainer/ppo/core_algos.py` |
| Trainer loop (steps, callbacks) | `verl/trainer/ppo/ray_trainer.py` |
| Metrics logging | `verl/trainer/ppo/metric_utils.py` |
| Main entry point & config | `verl/trainer/main_ppo.py` |
| Actor (data-parallel) | `verl/workers/actor/dp_actor.py` |
| FSDP workers | `verl/workers/fsdp_workers.py` |

---

## Quick Reference

```bash
# Create a new idea
bash research/bin/init_idea.sh <idea_id>

# Smoke test
bash research/bin/run_experiment.sh --recipe <R> --profile smoke --idea research/ideas/<id>

# Full run
bash research/bin/run_experiment.sh --recipe <R> --profile full --idea research/ideas/<id>

# Dry run (validate command without training)
bash research/bin/run_experiment.sh --recipe <R> --profile smoke --idea research/ideas/<id> --dry-run

# Generate report
python research/bin/gen_report.py --idea research/ideas/<id>

# Extra overrides (repeatable)
bash research/bin/run_experiment.sh --recipe <R> --profile smoke --idea research/ideas/<id> \
    --override key1=value1 --override key2=value2

# Set seed
bash research/bin/run_experiment.sh --recipe <R> --profile smoke --idea research/ideas/<id> --seed 42
```
