#!/bin/zsh
set -e
ROOT="/Users/masonstretch/Desktop/Trader Dashboard/trading_os"
cd "$ROOT"
export PYTHONPATH="$ROOT"
export DISCORD_WEBHOOK_URL='https://discord.com/api/webhooks/1534967748784947211/O5FynKL_WWDKLTt2PW4OwMGE96qkuFYsz-bPgiqa1ypzMVlDWKpWDsVRZIhThU7Mk6Ez'

case "$1" in
  pre)
    RUN_MODE=pre /Users/masonstretch/Desktop/Trader\ Dashboard/.venv/bin/python src/integrations/cron_runner.py
    ;;
  open)
    RUN_MODE=open /Users/masonstretch/Desktop/Trader\ Dashboard/.venv/bin/python src/integrations/cron_runner.py
    ;;
  midday)
    RUN_MODE=midday /Users/masonstretch/Desktop/Trader\ Dashboard/.venv/bin/python src/integrations/cron_runner.py
    ;;
  news)
    RUN_MODE=news /Users/masonstretch/Desktop/Trader\ Dashboard/.venv/bin/python src/integrations/cron_runner.py
    ;;
  *)
    RUN_MODE=full /Users/masonstretch/Desktop/Trader\ Dashboard/.venv/bin/python src/integrations/cron_runner.py
    ;;
esac
