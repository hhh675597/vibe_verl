# Higher Actor Learning Rate (5e-6)

## Source
Manual experiment — testing whether the default 1e-6 actor LR is too conservative for the small Qwen2.5-0.5B model on GSM8K.

## Hypothesis
A 5x higher actor learning rate (5e-6 vs 1e-6) will lead to faster reward improvement within the same number of training steps. The small model size should tolerate a higher LR without training instability.

## Plan
- [x] Understand the idea
- [x] Implement (config override only — no code changes)
- [ ] Smoke test
- [ ] Full run
- [ ] Compare with baseline
- [ ] Write report

## Code Changes
None — this is a config-only experiment.

## Log
<!-- Example entries:
- 2025-03-20 10:00  Created idea. Only config change needed: actor LR 1e-6 → 5e-6.
-->
