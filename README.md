# Research Harness

This directory contains a thin experiment harness around existing `verl` entrypoints.
It is intentionally external to `verl/` so that research-assistant automation does not
bleed into the training library itself.

## Scope

The first slice is intentionally small:

- define a recipe with a baseline command shape
- launch a run into a structured artifact directory
- rely on `verl`'s existing file metric logger and rollout/validation dumps
- summarize the run into a compact JSON report
- append a row into a JSONL ledger

This layer does **not** replace `verl` logging, checkpointing, or validation. It
simply standardizes how experiments are launched and how artifacts are organized.

## Layout

```text
research/
  bin/
    run_experiment.sh
    summarize_run.py
    append_ledger.py
  recipes/
    math_grpo_small/
      recipe.sh
      smoke.sh
      full.sh
  ledger/
    runs.jsonl        # created on demand
    best.json         # created on demand
  runs/               # local run artifacts, ignored by git
```

## Artifact Contract

Each run is written under `research/runs/<run_id>/` with this shape:

```text
research/runs/<run_id>/
  manifest.json
  command.sh
  driver.log
  metrics.jsonl
  summary.json
  rollouts/
  validation/
  checkpoints/
  env/
    git_head.txt
    git_status.txt
    git_diff.patch
    env.txt
    pwd.txt
    nvidia_smi.txt
```

Important wiring:

- `VERL_FILE_LOGGER_PATH` points to `metrics.jsonl`
- `trainer.rollout_data_dir` points to `rollouts/`
- `trainer.validation_data_dir` points to `validation/`
- `trainer.default_local_dir` points to `checkpoints/`

## Usage

Smoke test a recipe without actually launching:

```bash
bash research/bin/run_experiment.sh \
  --recipe math_grpo_small \
  --profile smoke \
  --dry-run
```

Launch a real run:

```bash
bash research/bin/run_experiment.sh \
  --recipe math_grpo_small \
  --profile smoke \
  --seed 1 \
  --note "baseline smoke test"
```

Pass extra Hydra overrides:

```bash
bash research/bin/run_experiment.sh \
  --recipe math_grpo_small \
  --profile full \
  --override actor_rollout_ref.actor.optim.lr=5e-7 \
  --override trainer.total_training_steps=20
```

Use an idea override file:

```bash
bash research/bin/run_experiment.sh \
  --recipe math_grpo_small \
  --profile full \
  --idea /abs/path/to/idea.overrides.sh
```

Idea files are optional shell snippets that define:

```bash
IDEA_ID="length_norm_grpo"
IDEA_OVERRIDES=(
  "actor_rollout_ref.actor.loss_agg_mode=seq-mean-token-sum-norm"
  "algorithm.norm_adv_by_std_in_grpo=False"
)
```

## Recipe Contract

Each recipe must define:

- `ENTRYPOINT`
- `PROJECT_NAME`
- `TRAINER_LOGGERS`
- `PRIMARY_METRIC_MODE`
- one of `PRIMARY_METRIC_KEY` or `PRIMARY_METRIC_PATTERN`
- `BASE_OVERRIDES` bash array

Each profile file must define:

- `PROFILE_NAME`
- `RUN_TIMEOUT_SECONDS`
- `PROFILE_OVERRIDES` bash array

## Notes

- This harness is deliberately shell-first and lightweight.
- The ledger uses JSONL instead of TSV because nested metadata and artifact paths are
  easier to preserve.
- The first slice does not yet include a dedicated failure classifier or run comparator.
