# MaxRL Reproduction On Math GRPO Recipe

## Source
- Paper: https://arxiv.org/abs/2602.02710
- Project page: https://zanette-labs.github.io/MaxRL/
- User request on 2026-03-22 to reproduce MaxRL in this VeRL checkout using the local DS-Distill-Qwen-1.5B model and math parquet files.

## Hypothesis
Replacing GRPO's standard-deviation-normalized group advantage with MaxRL's mean-reward-normalized estimator should improve the policy signal on sparse binary math rewards without changing the trainer loop. On this math setup, I expect MaxRL to emphasize prompt-level success probability more directly than GRPO and produce a cleaner pass@1 reward trajectory.

## Plan
- [x] Understand the idea
- [x] Implement (code changes and/or config overrides)
- [x] Smoke test
- [x] Full run
- [x] Write report

## Code Changes
### verl/trainer/ppo/core_algos.py
- Added `compute_maxrl_outcome_advantage()` implementing the paper's per-group mean reward normalization `(r - mean_r) / (mean_r + eps)`.

### verl/trainer/ppo/ray_trainer.py
- Added `AdvantageEstimator.MAXRL`.
- Routed `algorithm.adv_estimator=maxrl` through the new MaxRL advantage computation and treated it as a critic-free estimator like GRPO.

### tests/trainer/ppo/test_core_algos.py
- Added focused CPU tests for MaxRL group-mean normalization and zero-mean-group stability.

### research/ideas/maxrl_2602_02710/overrides.txt
- Pinned the idea to `algorithm.adv_estimator=maxrl`, the local DS-Distill-Qwen-1.5B model, the repo-local math parquet files, the `math` environment, and a smaller Ray CPU budget to avoid local-cluster startup timeouts.
- Enabled `data.return_raw_chat=True` so the env rollout path receives `raw_prompt`, which this repo's `TrajectoryCollector` expects during validation/training.
- Increased `ray_init.num_cpus` from 8 to 64 once the experiment moved to 8 GPUs; the smaller Ray CPU budget appeared to stall multi-GPU worker initialization.
- Reduced actor and log-prob micro-batches to `1` after the first 8-GPU full run hit CUDA OOM during `update_actor()`.

### research/recipes/math_grpo_small/smoke.sh
- Switched the smoke profile from overriding `actor_rollout_ref.rollout.n` to overriding `env.rollout.n`, which matches this repo's `main_ppo.py` contract (`actor_rollout_ref.rollout.n` must stay at `1`).
- Disabled pre-train/step validation in smoke (`trainer.val_before_train=False`, `trainer.test_freq=-1`) so smoke exercises trainer startup and updates quickly instead of spending most of its time validating 960 examples.

### verl/utils/tracking.py
- Restored a minimal `file` tracking backend that writes line-delimited JSON records to `VERL_FILE_LOGGER_PATH`, which is what the research harness expects for `metrics.jsonl`.
- Guarded `Tracking.__del__()` so unsupported-backend failures do not emit a secondary attribute error during cleanup.

### research/recipes/math_grpo_small/recipe.sh
- Restored the default logger list to `['wandb','file']` after adding back file logging support, so future runs publish to WANDB while still emitting local `metrics.jsonl`.
- Corrected the math environment selector from `env.name=math` to `env.env_name=math` so Hydra resolves the right config key in this repo.
- Updated the recipe default from `trainer.n_gpus_per_node=1` to `8` after confirming this machine exposes 8 H100 80GB GPUs and the user wants the run to use them.
- Updated `PRIMARY_METRIC_PATTERN` to `^val/.+/test_score$` so future math runs track the actual validation metric instead of the stale `val-core/.../reward` pattern.

### research/recipes/math_grpo_small/full.sh
- Reduced full-run validation overhead by disabling `val_before_train` and setting `trainer.test_freq` to `${FULL_TEST_FREQ:-25}`.

## Log
- 2026-03-22 10:29 CST  Recreated the idea workspace after the prior `research/ideas/maxrl_2602_02710/` directory had been deleted from the worktree.
- 2026-03-22 10:29 CST  Confirmed from the MaxRL paper/project page that the on-policy VeRL implementation replaces GRPO's per-group std normalization with per-group mean reward normalization.
- 2026-03-22 10:29 CST  Verified the local DS-Distill-Qwen-1.5B model path exists. The hard-coded `data/math/...` recipe paths do not exist in this checkout, but repo-local math parquet files do exist at `data/train.parquet` and `data/test.parquet`.
- 2026-03-22 10:31 CST  MaxRL code compiled with `python -m py_compile`, and the focused unit test `tests.trainer.ppo.test_core_algos` passed under the `vibe-verl` environment.
- 2026-03-22 10:31 CST  Dry-run smoke succeeded. The generated command resolved `algorithm.adv_estimator=maxrl` and correctly overrode the broken recipe data paths with the repo-local parquet files.
- 2026-03-22 10:32 CST  First smoke attempt failed inside the sandbox at `ray.init` with `PermissionError: [Errno 1] Operation not permitted` when Ray opened its local socket.
- 2026-03-22 10:34 CST  Re-ran smoke outside the sandbox. Ray started, but the run still failed before training because the local Ray runtime-env agent timed out while the recipe requested `ray_init.num_cpus=96`.
- 2026-03-22 10:34 CST  Diagnosed a second harness issue: this repo's `main_ppo.py` requires `actor_rollout_ref.rollout.n == 1`, so the smoke profile must scale `env.rollout.n` instead. Reduced the idea's Ray CPU budget to 8 and patched the smoke profile accordingly before retrying.
- 2026-03-22 10:40 CST  Retried smoke with the Ray/rollout fixes and reached trainer initialization, which exposed a third config issue: `math_grpo_small` never selected the math environment and was silently falling back to `alfworld/AlfredTWEnv`. Added `env.env_name=math` and `env.max_steps=1` to the idea overrides before the next relaunch.
- 2026-03-22 10:43 CST  The next smoke failure reached `trainer.fit()` and exposed a harness/code mismatch: `run_experiment.sh` injects `trainer.logger=['wandb','file']`, but `verl/utils/tracking.py` in this checkout did not implement the `file` backend. Restored local file logging and changed the recipe default to `['console','file']`.
- 2026-03-22 10:44 CST  Compared the local file logger against the upstream `volcengine/verl` implementation and aligned it to the official `FileLogger(project_name, experiment_name)` interface with the same `VERL_FILE_LOGGER_PATH` / `VERL_FILE_LOGGER_ROOT` behavior.
- 2026-03-22 10:45 CST  The next smoke launch failed immediately in Hydra because `math_grpo_small/recipe.sh` still contained `env.name=math`. Corrected that base override to `env.env_name=math`.
- 2026-03-22 10:46 CST  The next smoke launch reached validation in the math environment and failed in `TrajectoryCollector.preprocess_single_sample()` because `gen_batch.non_tensor_batch['raw_prompt']` was missing. Added `data.return_raw_chat=True` to the idea overrides so the dataset includes that field.
- 2026-03-22 10:49 CST  The next smoke launch cleared the `raw_prompt` issue and entered real validation/training, but it spent almost all of its time walking the full validation set because smoke still had `val_before_train=True` and `test_freq=1`. Stopped that run and reduced validation frequency in both smoke and full profiles.
- 2026-03-22 10:58 CST  Smoke passed on run `20260322_105451_math_grpo_small_smoke_maxrl_2602_02710_s1`. The trainer completed 2 steps, wrote `metrics.jsonl`, and dumped 2 rollout files.
- 2026-03-22 10:58 CST  Per user request, restored the next-run logger default to `['wandb','file']` now that the local file backend matches the upstream VeRL interface.
- 2026-03-22 11:03 CST  Confirmed the node has 8x NVIDIA H100 80GB GPUs. The first full-run attempt was still using `trainer.n_gpus_per_node=1`, so I updated the recipe to default to all 8 GPUs before relaunching full.
- 2026-03-22 11:12 CST  The 8-GPU full run still hung before worker initialization finished while `ray_init.num_cpus=8` remained in the idea overrides. Per user suggestion, increased the Ray CPU budget to 64 before the next full-run relaunch.
- 2026-03-22 11:20 CST  The next 8-GPU/64-CPU full run progressed into real training but failed in `actor_rollout_wg.update_actor()` with CUDA OOM (`ppo_micro_batch_size_per_gpu=8`). Reduced actor and log-prob micro-batches to 1 before the next retry.
- 2026-03-22 12:27 CST  Current full run `20260322_112008_math_grpo_small_full_maxrl_2602_02710_s1` is healthy on 8 H100s with `ray_init.num_cpus=64` and micro-batches of 1. It has reached step 27/50, written 27 metric records and 27 rollout shards, and logged `val/aime24/test_score=0.13333333333333333` at step 25.
- 2026-03-22 13:01 CST  Full run `20260322_112008_math_grpo_small_full_maxrl_2602_02710_s1` has reached step 42/50. Recent training remains stable: reward mean has been hovering around 0.39-0.43, throughput around 2.8k-3.4k tokens/s, and no new OOM or worker-init failures have appeared after the 8-GPU / 64-CPU / micro-batch-1 adjustments.
- 2026-03-22 13:24 CST  Full run `20260322_112008_math_grpo_small_full_maxrl_2602_02710_s1` finished successfully in 7242s. Validation improved from `val/aime24/test_score=0.13333333333333333` at step 25 to `0.16666666666666666` at step 50. Final training reward mean was `0.48046875`; average throughput over the run's later stable region was roughly 3.0k tokens/s on 8 H100s.
