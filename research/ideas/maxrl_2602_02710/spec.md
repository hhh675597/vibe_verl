# MaxRL Reproduction On Math GRPO Recipe

## Source
- Paper: https://arxiv.org/abs/2602.02710
- Project page: https://zanette-labs.github.io/MaxRL/
- Reference implementation: https://raw.githubusercontent.com/tajwarfahim/maxrl/main/verl/trainer/ppo/core_algos.py
- User request on 2026-03-21 to reproduce MaxRL with `models/DS-Distill-Qwen-1.5B` on the local math parquet files.

## Hypothesis
Replacing GRPO's standard-deviation-normalized group advantage with MaxRL's mean-reward-normalized estimator should improve learning signal on sparse binary math rewards without requiring trainer-loop changes. On this math setup, I expect MaxRL to produce a cleaner pass@1 reward signal than the existing GRPO baseline because the estimator directly emphasizes success probability within each prompt group.

## Plan
- [x] Understand the idea
- [x] Implement (code changes and/or config overrides)
- [ ] Smoke test
- [ ] Full run
- [ ] Write report

## Code Changes
### verl/trainer/ppo/core_algos.py
- Added `AdvantageEstimator.MAXRL`.
- Added `compute_maxrl_outcome_advantage()` using the paper's per-group mean normalization `(r - mean_r) / (mean_r + eps)`.

### tests/trainer/ppo/test_core_algos_on_cpu.py
- Added a unit test covering the MaxRL estimator's group-mean normalization behavior and zero-mean group stability.

### tests/trainer/config/test_algo_config_on_cpu.py
- Added a config integration test that resolves `adv_estimator=maxrl` and checks the resulting advantages.

### research/ideas/maxrl_2602_02710/overrides.txt
- Pinned the idea to `algorithm.adv_estimator=maxrl`, the provided local model, and the local math train/test parquet files.

### research/env.sh
- Made `ray stop --force` best-effort so environment teardown failures do not abort experiments before trainer startup.

## Log
- 2026-03-21 22:31 CST  Created the idea workspace. Confirmed from the paper/project code that MaxRL uses the per-group estimator `(r - mean_r) / (mean_r + eps)`.
- 2026-03-21 22:31 CST  Verified the local experiment assets: model path exists, math data exists as `data/math/train.parquet` and `data/math/test.parquet`. The requested `data/math/training.parquet` path is not present in this checkout.
- 2026-03-21 22:33 CST  Implemented `maxrl` in `verl/trainer/ppo/core_algos.py`, added focused unit coverage, and verified the edited Python files compile with `python -m py_compile`. `pytest` is not installed in the repo env, so I could not run the pytest suite directly.
- 2026-03-21 22:34 CST  Dry-run smoke succeeded. Harness materialized the MaxRL command and run directory correctly.
- 2026-03-21 22:34 CST  Smoke failed before trainer startup because `ray stop --force` in `research/env.sh` crashed inside the Ray CLI (`ValueError: <object object ...> is not a valid Sentinel`). Made Ray teardown best-effort.
- 2026-03-21 22:35 CST  Smoke failed again inside the workspace sandbox when Ray attempted to open a socket during `ray.init` (`PermissionError: [Errno 1] Operation not permitted`). Next smoke attempt must run with escalated permissions.
