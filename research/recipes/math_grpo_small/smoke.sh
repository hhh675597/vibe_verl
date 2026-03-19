#!/usr/bin/env bash

PROFILE_NAME="smoke"
RUN_TIMEOUT_SECONDS="${RUN_TIMEOUT_SECONDS:-1800}"

SMOKE_TOTAL_TRAINING_STEPS="${SMOKE_TOTAL_TRAINING_STEPS:-2}"
SMOKE_TRAIN_BATCH_SIZE="${SMOKE_TRAIN_BATCH_SIZE:-2}"
SMOKE_VAL_BATCH_SIZE="${SMOKE_VAL_BATCH_SIZE:-2}"
SMOKE_ROLLOUT_N="${SMOKE_ROLLOUT_N:-2}"

PROFILE_OVERRIDES=(
  "data.train_batch_size=${SMOKE_TRAIN_BATCH_SIZE}"
  "data.val_batch_size=${SMOKE_VAL_BATCH_SIZE}"
  "actor_rollout_ref.rollout.n=${SMOKE_ROLLOUT_N}"
  "actor_rollout_ref.actor.ppo_mini_batch_size=4"
  "actor_rollout_ref.actor.ppo_micro_batch_size_per_gpu=1"
  "actor_rollout_ref.rollout.log_prob_micro_batch_size_per_gpu=1"
  "actor_rollout_ref.ref.log_prob_micro_batch_size_per_gpu=1"
  "trainer.test_freq=1"
  "trainer.save_freq=-1"
  "trainer.total_training_steps=${SMOKE_TOTAL_TRAINING_STEPS}"
)
