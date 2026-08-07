#!/usr/bin/env python3
"""Build the public Signal Bridge static site artifact for GitHub Pages."""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "_site"
EXPORT_SCRIPT = ROOT / "trading_os" / "src" / "integrations" / "export_shareable_dashboard.py"
SHAREABLE = ROOT / "share" / "signal_bridge_premium_shareable.html"
REPORT = ROOT / "trading_os" / "src" / "integrations" / "report.json"


def copy_if_exists(source: Path, destination: Path) -> None:
    if not source.exists():
        return
    destination.parent.mkdir(parents=True, exist_ok=True)
    if source.is_dir():
        shutil.copytree(source, destination, dirs_exist_ok=True)
    else:
        shutil.copy2(source, destination)


def main() -> int:
    if SITE.exists():
        shutil.rmtree(SITE)
    SITE.mkdir(parents=True)

    # Rebuild the standalone dashboard from the checked-in report snapshot so the
    # deployed page does not depend on a local Python server just to render.
    subprocess.run([sys.executable, str(EXPORT_SCRIPT)], cwd=ROOT, check=True)
    if not SHAREABLE.exists():
        raise FileNotFoundError(f"Shareable dashboard was not generated: {SHAREABLE}")

    shutil.copy2(SHAREABLE, SITE / "index.html")
    copy_if_exists(ROOT / "assets", SITE / "assets")
    copy_if_exists(ROOT / "manifest.json", SITE / "manifest.json")
    copy_if_exists(ROOT / "metadata.json", SITE / "metadata.json")
    copy_if_exists(REPORT, SITE / "report.json")
    copy_if_exists(ROOT / "share" / "signal_bridge_report.json", SITE / "signal_bridge_report.json")

    # Prevent Jekyll processing from altering asset paths.
    (SITE / ".nojekyll").write_text("", encoding="utf-8")

    required = [SITE / "index.html", SITE / "report.json"]
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        raise FileNotFoundError(f"Missing required Pages outputs: {missing}")

    print(f"Built Signal Bridge Pages artifact at {SITE}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
