# Machine-level environment for research harness.
# This file is inlined into every command.sh before the training command.
# Ray teardown is best-effort here; some environments fail inside the CLI before
# any training command runs, and we do not want that to abort experiments.
ray stop --force >/dev/null 2>&1 || true
unset ROCR_VISIBLE_DEVICES
unset HIP_VISIBLE_DEVICES

export CUDA_VISIBLE_DEVICES=0,1,2,3,4,5,6,7
export WANDB_BASE_URL=https://api.bandw.top
export WANDB_API_KEY=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
