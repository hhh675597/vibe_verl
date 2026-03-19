# Research Assistant Workflow

You are a research assistant for LLM RL post-training experiments using verl.

## The Loop
1. Understand the idea (what hypothesis, how to implement the proposed training pipeline or loss function)
2. Determine if the idea is config-only (-> idea.overrides.sh) or requires code changes
3. Smoke test first: `bash research/bin/run_experiment.sh --recipe <R> --profile smoke --idea <path>`
4. Read `<run_dir>/driver.log` and `<run_dir>/summary.json` to check for errors
5. If failed: diagnose from driver.log, fix, re-run smoke
6. If smoke passes: run full: `bash research/bin/run_experiment.sh --recipe <R> --profile full --idea <path>`
7. Compare results against baseline in `research/ledger/best.json`
8. Report findings

## Key Files
- Recipes live in `research/recipes/<name>/recipe.sh`
- Profiles: `smoke.sh` (fast validation), `full.sh` (real experiment)
- Ideas: shell files defining IDEA_ID and IDEA_OVERRIDES
- Run artifacts: `research/runs/<run_id>/`
- Ledger: `research/ledger/runs.jsonl` (all runs), `research/ledger/best.json` (per-recipe best)

## Debugging a Failed Run
- Read `<run_dir>/driver.log` (full log) or `summary.json` -> `driver_log_tail`
- Common failures: OOM -> reduce batch size; CUDA error -> check GPU state; Hydra error -> fix overrides
- Key files to debug: verl/trainer/ppo/ray_trainer.py; verl/trainer/main_ppo.py; verl/trainer/ppo/core_algos.py;  verl/workers/actor/dp_actor.py; verl/works/fsdp_workers.py
- Exit code 124 = timeout

## Where to Make Code Changes
- Reward functions: verl/utils/reward_score/...
- Loss computation: verl/trainer/ppo/core_algos.py
- Trainer loop: verl/trainer/ppo/ray_trainer.py
- Metrics: verl/trainer/ppo/metric_utils.py
- Main entry point: verl/trainer/main_ppo.py