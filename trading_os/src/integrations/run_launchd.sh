#!/bin/zsh
set -euo pipefail

SCRIPT_DIR="${0:A:h}"
TRADING_OS_ROOT="${SCRIPT_DIR:h:h}"
REPO_ROOT="${TRADING_OS_ROOT:h}"

if [[ -f "$REPO_ROOT/.env.local" ]]; then
  set -a
  source "$REPO_ROOT/.env.local"
  set +a
fi

if [[ -x "$REPO_ROOT/.venv/bin/python" ]]; then
  PYTHON="$REPO_ROOT/.venv/bin/python"
elif command -v python3 >/dev/null 2>&1; then
  PYTHON="$(command -v python3)"
else
  echo "Signal Bridge: python3 not found" >&2
  exit 1
fi

export PYTHONPATH="$TRADING_OS_ROOT"
cd "$TRADING_OS_ROOT"
exec "$PYTHON" "$SCRIPT_DIR/cron_runner.py"
