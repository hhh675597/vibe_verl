#!/usr/bin/env bash

PROFILE_NAME="full"
RUN_TIMEOUT_SECONDS="${RUN_TIMEOUT_SECONDS:-14400}"

FULL_TOTAL_TRAINING_STEPS="${FULL_TOTAL_TRAINING_STEPS:-50}"
FULL_TEST_FREQ="${FULL_TEST_FREQ:-25}"

PROFILE_OVERRIDES=(
  "trainer.val_before_train=False"
  "trainer.test_freq=${FULL_TEST_FREQ}"
  "trainer.total_training_steps=${FULL_TOTAL_TRAINING_STEPS}"
)
