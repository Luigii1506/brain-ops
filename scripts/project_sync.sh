#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PROJECT_NAME="${BRAIN_OPS_PROJECT_NAME:-brain-ops}"
CONFIG_PATH="${BRAIN_OPS_CONFIG_PATH:-$REPO_ROOT/config/vault.yaml}"

if ! command -v brain >/dev/null 2>&1; then
  exit 0
fi

SYNC_CMD=(brain refresh-project "$PROJECT_NAME" --config "$CONFIG_PATH")

if [ "${BRAIN_OPS_SYNC_DRY_RUN:-0}" = "1" ]; then
  printf 'Would run:'
  printf ' %q' "${SYNC_CMD[@]}"
  printf '\n'
  exit 0
fi

"${SYNC_CMD[@]}" >/dev/null 2>&1 || true
