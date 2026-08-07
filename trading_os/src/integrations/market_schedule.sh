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

case "${1:-full}" in
  pre|open|midday|news|full)
    export RUN_MODE="${1:-full}"
    ;;
  *)
    echo "Usage: market_schedule.sh [pre|open|midday|news|full]" >&2
    exit 2
    ;;
esac

exec /bin/zsh "$SCRIPT_DIR/run_launchd.sh"
