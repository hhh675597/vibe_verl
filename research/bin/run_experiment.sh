#!/usr/bin/env bash

set -euo pipefail

usage() {
    cat <<'EOF'
Usage:
  bash research/bin/run_experiment.sh --recipe NAME --profile NAME [options]

Options:
  --recipe NAME           Recipe name under research/recipes/
  --profile NAME          Profile file under the recipe directory, e.g. smoke or full
  --idea PATH             Optional shell file defining IDEA_ID and IDEA_OVERRIDES
  --seed INT              Random seed recorded in the manifest and passed through if the recipe supports it
  --note TEXT             Free-form note recorded in the manifest and ledger
  --override KEY=VALUE    Extra Hydra override, may be passed multiple times
  --dry-run               Materialize artifacts and command without launching training
  --help                  Show this message
EOF
}

die() {
    echo "error: $*" >&2
    exit 1
}

slugify() {
    echo "$1" | tr '[:upper:]' '[:lower:]' | sed -E 's/[^a-z0-9._-]+/-/g; s/^-+//; s/-+$//'
}

resolve_path() {
    local path="$1"
    if [[ "$path" = /* ]]; then
        echo "$path"
    else
        echo "$PWD/$path"
    fi
}

RECIPE=""
PROFILE=""
IDEA_PATH=""
SEED="${SEED:-1}"
NOTE=""
DRY_RUN=0
EXTRA_OVERRIDES=()

while [[ $# -gt 0 ]]; do
    case "$1" in
        --recipe)
            RECIPE="${2:-}"
            shift 2
            ;;
        --profile)
            PROFILE="${2:-}"
            shift 2
            ;;
        --idea)
            IDEA_PATH="${2:-}"
            shift 2
            ;;
        --seed)
            SEED="${2:-}"
            shift 2
            ;;
        --note)
            NOTE="${2:-}"
            shift 2
            ;;
        --override)
            EXTRA_OVERRIDES+=("${2:-}")
            shift 2
            ;;
        --dry-run)
            DRY_RUN=1
            shift
            ;;
        --help|-h)
            usage
            exit 0
            ;;
        *)
            die "unknown argument: $1"
            ;;
    esac
done

[[ -n "$RECIPE" ]] || die "--recipe is required"
[[ -n "$PROFILE" ]] || die "--profile is required"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RESEARCH_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
REPO_ROOT="$(cd "${RESEARCH_ROOT}/.." && pwd)"

RECIPE_DIR="${RESEARCH_ROOT}/recipes/${RECIPE}"
RECIPE_FILE="${RECIPE_DIR}/recipe.sh"
PROFILE_FILE="${RECIPE_DIR}/${PROFILE}.sh"

[[ -f "$RECIPE_FILE" ]] || die "recipe file not found: $RECIPE_FILE"
[[ -f "$PROFILE_FILE" ]] || die "profile file not found: $PROFILE_FILE"

# shellcheck source=/dev/null
source "$RECIPE_FILE"
# shellcheck source=/dev/null
source "$PROFILE_FILE"

IDEA_ID=""
IDEA_OVERRIDES=()
if [[ -n "$IDEA_PATH" ]]; then
    IDEA_PATH="$(resolve_path "$IDEA_PATH")"
    [[ -f "$IDEA_PATH" ]] || die "idea file not found: $IDEA_PATH"
    # shellcheck source=/dev/null
    source "$IDEA_PATH"
fi

ENTRYPOINT="${ENTRYPOINT:-verl.trainer.main_ppo}"
PROJECT_NAME="${PROJECT_NAME:-research_${RECIPE}}"
TRAINER_LOGGERS="${TRAINER_LOGGERS:-['console','file']}"
PRIMARY_METRIC_KEY="${PRIMARY_METRIC_KEY:-}"
PRIMARY_METRIC_PATTERN="${PRIMARY_METRIC_PATTERN:-}"
PRIMARY_METRIC_MODE="${PRIMARY_METRIC_MODE:-max}"
RUN_TIMEOUT_SECONDS="${RUN_TIMEOUT_SECONDS:-3600}"
PYTHON_BIN="${PYTHON_BIN:-python3}"
PROFILE_NAME="${PROFILE_NAME:-$PROFILE}"
IDEA_ID="${IDEA_ID:-baseline}"

[[ -n "$PRIMARY_METRIC_KEY" || -n "$PRIMARY_METRIC_PATTERN" ]] || die "recipe must define a primary metric key or pattern"

RUN_TS="$(date +%Y%m%d_%H%M%S)"
RUN_ID="$(slugify "${RUN_TS}_${RECIPE}_${PROFILE_NAME}_${IDEA_ID}_s${SEED}")"
RUN_DIR="${RESEARCH_ROOT}/runs/${RUN_ID}"
ENV_DIR="${RUN_DIR}/env"
ROLL_OUT_DIR="${RUN_DIR}/rollouts"
VALIDATION_DIR="${RUN_DIR}/validation"
CHECKPOINT_DIR="${RUN_DIR}/checkpoints"
HYDRA_DIR="${RUN_DIR}/hydra"
DRIVER_LOG="${RUN_DIR}/driver.log"
METRICS_PATH="${RUN_DIR}/metrics.jsonl"
SUMMARY_PATH="${RUN_DIR}/summary.json"
MANIFEST_PATH="${RUN_DIR}/manifest.json"
COMMAND_PATH="${RUN_DIR}/command.sh"
LEDGER_PATH="${RESEARCH_ROOT}/ledger/runs.jsonl"
BEST_PATH="${RESEARCH_ROOT}/ledger/best.json"

mkdir -p "$RUN_DIR" "$ENV_DIR" "$ROLL_OUT_DIR" "$VALIDATION_DIR" "$CHECKPOINT_DIR" "${RESEARCH_ROOT}/ledger"

printf '%s\n' "$PWD" > "${ENV_DIR}/pwd.txt"
git -C "$REPO_ROOT" rev-parse HEAD > "${ENV_DIR}/git_head.txt" 2>&1 || true
git -C "$REPO_ROOT" status --short > "${ENV_DIR}/git_status.txt" 2>&1 || true
git -C "$REPO_ROOT" diff --binary > "${ENV_DIR}/git_diff.patch" 2>&1 || true
env | sort > "${ENV_DIR}/env.txt"
nvidia-smi > "${ENV_DIR}/nvidia_smi.txt" 2>&1 || true

MANDATORY_OVERRIDES=(
    "trainer.project_name=${PROJECT_NAME}"
    "trainer.experiment_name=${RUN_ID}"
    "trainer.logger=${TRAINER_LOGGERS}"
    "trainer.rollout_data_dir=${ROLL_OUT_DIR}"
    "trainer.validation_data_dir=${VALIDATION_DIR}"
    "trainer.default_local_dir=${CHECKPOINT_DIR}"
    "hydra.run.dir=${HYDRA_DIR}"
    "hydra.job.chdir=False"
    "trainer.seed=${SEED}"
)

CMD=("$PYTHON_BIN" "-m" "$ENTRYPOINT")
for override in "${BASE_OVERRIDES[@]}" "${PROFILE_OVERRIDES[@]}" "${IDEA_OVERRIDES[@]}" "${EXTRA_OVERRIDES[@]}" "${MANDATORY_OVERRIDES[@]}"; do
    [[ -n "$override" ]] || continue
    CMD+=("$override")
done

{
    echo "#!/usr/bin/env bash"
    echo "set -euo pipefail"
    printf 'export PYTHONUNBUFFERED=%q\n' "1"
    printf 'export VERL_FILE_LOGGER_PATH=%q\n' "$METRICS_PATH"
    printf 'cd %q\n' "$REPO_ROOT"
    printf '%q ' "${CMD[@]}"
    echo '"$@"'
} > "$COMMAND_PATH"
chmod +x "$COMMAND_PATH"

BASE_OVERRIDES_NL="$(printf '%s\n' "${BASE_OVERRIDES[@]}")"
PROFILE_OVERRIDES_NL="$(printf '%s\n' "${PROFILE_OVERRIDES[@]}")"
IDEA_OVERRIDES_NL="$(printf '%s\n' "${IDEA_OVERRIDES[@]}")"
EXTRA_OVERRIDES_NL="$(printf '%s\n' "${EXTRA_OVERRIDES[@]}")"
MANDATORY_OVERRIDES_NL="$(printf '%s\n' "${MANDATORY_OVERRIDES[@]}")"

export RUN_ID RECIPE PROFILE_NAME IDEA_ID SEED NOTE ENTRYPOINT PROJECT_NAME
export PRIMARY_METRIC_KEY PRIMARY_METRIC_PATTERN PRIMARY_METRIC_MODE RUN_TIMEOUT_SECONDS
export MANIFEST_PATH DRIVER_LOG METRICS_PATH ROLL_OUT_DIR VALIDATION_DIR CHECKPOINT_DIR HYDRA_DIR COMMAND_PATH
export BASE_OVERRIDES_NL PROFILE_OVERRIDES_NL IDEA_OVERRIDES_NL EXTRA_OVERRIDES_NL MANDATORY_OVERRIDES_NL

"$PYTHON_BIN" - <<'PY'
import json
import os


def to_list(name: str) -> list[str]:
    raw = os.environ.get(name, "")
    return [line for line in raw.splitlines() if line]


manifest = {
    "run_id": os.environ["RUN_ID"],
    "recipe": os.environ["RECIPE"],
    "profile": os.environ["PROFILE_NAME"],
    "idea_id": os.environ["IDEA_ID"],
    "seed": int(os.environ["SEED"]),
    "note": os.environ.get("NOTE", ""),
    "entrypoint": os.environ["ENTRYPOINT"],
    "project_name": os.environ["PROJECT_NAME"],
    "primary_metric_key": os.environ.get("PRIMARY_METRIC_KEY", ""),
    "primary_metric_pattern": os.environ.get("PRIMARY_METRIC_PATTERN", ""),
    "primary_metric_mode": os.environ["PRIMARY_METRIC_MODE"],
    "timeout_seconds": int(os.environ["RUN_TIMEOUT_SECONDS"]),
    "artifacts": {
        "driver_log": os.environ["DRIVER_LOG"],
        "metrics": os.environ["METRICS_PATH"],
        "rollouts": os.environ["ROLL_OUT_DIR"],
        "validation": os.environ["VALIDATION_DIR"],
        "checkpoints": os.environ["CHECKPOINT_DIR"],
        "hydra": os.environ["HYDRA_DIR"],
        "command": os.environ["COMMAND_PATH"],
    },
    "overrides": {
        "base": to_list("BASE_OVERRIDES_NL"),
        "profile": to_list("PROFILE_OVERRIDES_NL"),
        "idea": to_list("IDEA_OVERRIDES_NL"),
        "extra": to_list("EXTRA_OVERRIDES_NL"),
        "mandatory": to_list("MANDATORY_OVERRIDES_NL"),
    },
}

with open(os.environ["MANIFEST_PATH"], "w", encoding="utf-8") as f:
    json.dump(manifest, f, indent=2, sort_keys=True)
    f.write("\n")
PY

echo "run_id: ${RUN_ID}"
echo "run_dir: ${RUN_DIR}"
echo "command: ${COMMAND_PATH}"

if [[ "$DRY_RUN" -eq 1 ]]; then
    echo "dry_run: true"
    exit 0
fi

START_EPOCH="$(date +%s)"
set +e
if command -v timeout >/dev/null 2>&1; then
    timeout "${RUN_TIMEOUT_SECONDS}s" bash "$COMMAND_PATH" > "$DRIVER_LOG" 2>&1
    EXIT_CODE=$?
else
    bash "$COMMAND_PATH" > "$DRIVER_LOG" 2>&1
    EXIT_CODE=$?
fi
set -e
END_EPOCH="$(date +%s)"
DURATION_SECONDS="$((END_EPOCH - START_EPOCH))"

"$PYTHON_BIN" "${RESEARCH_ROOT}/bin/summarize_run.py" \
    --run-dir "$RUN_DIR" \
    --exit-code "$EXIT_CODE" \
    --duration-sec "$DURATION_SECONDS"

"$PYTHON_BIN" "${RESEARCH_ROOT}/bin/append_ledger.py" \
    --manifest "$MANIFEST_PATH" \
    --summary "$SUMMARY_PATH" \
    --ledger "$LEDGER_PATH" \
    --best "$BEST_PATH"

"$PYTHON_BIN" - "$SUMMARY_PATH" <<'PY'
import json
import sys

with open(sys.argv[1], "r", encoding="utf-8") as f:
    summary = json.load(f)

print(f"status: {summary['status']}")
print(f"best_primary_metric: {summary.get('best_primary_metric')}")
print(f"best_primary_metric_step: {summary.get('best_primary_metric_step')}")
print(f"primary_metric_key: {summary.get('primary_metric_key')}")
print(f"duration_sec: {summary.get('duration_sec')}")
print(f"rollout_files: {summary.get('rollout_files')}")
print(f"validation_files: {summary.get('validation_files')}")
PY

exit "$EXIT_CODE"
