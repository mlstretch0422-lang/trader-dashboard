import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def main():
    env = os.environ.copy()
    env.setdefault("PYTHONPATH", str(ROOT))
    mode = (os.getenv("RUN_MODE") or "full").lower()

    # Scheduled jobs generate research/context briefs only.
    # Real trade/event delivery is event-driven through serve_signal_bridge.py.
    if mode == "pre":
        commands = [
            [sys.executable, str(ROOT / "src" / "integrations" / "live_market_brief.py")],
            [sys.executable, str(ROOT / "src" / "integrations" / "daily_brief.py")],
        ]
    elif mode == "open":
        commands = [
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
            [sys.executable, str(ROOT / "src" / "integrations" / "live_market_brief.py")],
            [sys.executable, str(ROOT / "src" / "integrations" / "daily_brief.py")],
            [sys.executable, str(ROOT / "src" / "integrations" / "news_calendar_brief.py")],
        ]

    failures = []
    for command in commands:
        completed = subprocess.run(command, cwd=str(ROOT), env=env, check=False)
        if completed.returncode != 0:
            failures.append({"command": command[-1], "returncode": completed.returncode})

    if failures:
        raise SystemExit(f"Signal Bridge scheduled jobs failed: {failures}")


if __name__ == "__main__":
    main()
