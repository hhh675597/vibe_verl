# Machine-level environment for research harness.
# This file is inlined into every command.sh before the training command.
#
# Examples:
#   export WANDB_API_KEY="your-key-here"
#   export WANDB_PROJECT="verl-research"
#   export NCCL_DEBUG=INFO
#   module load cuda/12.1
#   ray stop --force >/dev/null 2>&1 || true
