import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def main():
    env = os.environ.copy()
    env.setdefault("PYTHONPATH", str(ROOT))
    mode = (os.getenv("RUN_MODE") or "full").lower()

    if mode == "pre":
        commands = [
            [sys.executable, str(ROOT / "src" / "integrations" / "live_market_brief.py")],
            [sys.executable, str(ROOT / "src" / "integrations" / "daily_brief.py")],
        ]
    elif mode == "open":
        commands = [
            [sys.executable, str(ROOT / "src" / "integrations" / "run_signal_bridge.py")],
            [sys.executable, str(ROOT / "src" / "integrations" / "live_market_brief.py")],
            [sys.executable, str(ROOT / "src" / "integrations" / "daily_brief.py")],
        ]
    elif mode == "midday":
        commands = [
            [sys.executable, str(ROOT / "src" / "integrations" / "live_market_brief.py")],
            [sys.executable, str(ROOT / "src" / "integrations" / "daily_brief.py")],
        ]
    elif mode == "news":
        commands = [
            [sys.executable, str(ROOT / "src" / "integrations" / "news_calendar_brief.py")],
        ]
    else:
        commands = [
            [sys.executable, str(ROOT / "src" / "integrations" / "run_signal_bridge.py")],
            [sys.executable, str(ROOT / "src" / "integrations" / "live_market_brief.py")],
            [sys.executable, str(ROOT / "src" / "integrations" / "daily_brief.py")],
            [sys.executable, str(ROOT / "src" / "integrations" / "news_calendar_brief.py")],
        ]

    for command in commands:
        subprocess.run(command, cwd=str(ROOT), env=env, check=False)


if __name__ == "__main__":
    main()
