#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PROJECT_NAME="${BRAIN_OPS_PROJECT_NAME:-brain-ops}"
CONFIG_PATH="${BRAIN_OPS_CONFIG_PATH:-$REPO_ROOT/config/vault.yaml}"
SYNC_SCRIPT="$REPO_ROOT/scripts/project_sync.sh"

if ! command -v git >/dev/null 2>&1; then
  exit 0
fi

if ! command -v brain >/dev/null 2>&1; then
  exit 0
fi

COMMIT_MSG="$(git -C "$REPO_ROOT" log -1 --pretty=%s 2>/dev/null || true)"
if [ -z "$COMMIT_MSG" ]; then
  exit 0
fi

LOG_CMD=(brain project-log "$PROJECT_NAME" "commit: $COMMIT_MSG" --config "$CONFIG_PATH")
REFRESH_CMD=(brain refresh-project "$PROJECT_NAME" --config "$CONFIG_PATH")

if [ "${BRAIN_OPS_POST_COMMIT_DRY_RUN:-0}" = "1" ]; then
  printf 'Would run:'
  printf ' %q' "${LOG_CMD[@]}"
  printf '\n'
  printf 'Would run:'
  printf ' %q' "${REFRESH_CMD[@]}"
  printf '\n'
  exit 0
fi

"${LOG_CMD[@]}" >/dev/null 2>&1 || true
if [ -x "$SYNC_SCRIPT" ]; then
  "$SYNC_SCRIPT"
else
  "${REFRESH_CMD[@]}" >/dev/null 2>&1 || true
fi
