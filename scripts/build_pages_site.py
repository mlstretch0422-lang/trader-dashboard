#!/usr/bin/env python3
"""Build the Signal Bridge Premium OS static artifact for GitHub Pages."""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "_site"
SITE_SOURCE = ROOT / "site"
EXPORT_SCRIPT = ROOT / "trading_os" / "src" / "integrations" / "export_shareable_dashboard.py"
SHAREABLE = ROOT / "share" / "signal_bridge_premium_shareable.html"
REPORT = ROOT / "trading_os" / "src" / "integrations" / "report.json"
RESEARCH_IMAGES = [
    ROOT / "SPX500_2026-07-08_10-23-12.png",
    ROOT / "Tradezella-Summary-June-26-2026.png",
]


def copy_if_exists(source: Path, destination: Path) -> None:
    if not source.exists():
        return
    destination.parent.mkdir(parents=True, exist_ok=True)
    if source.is_dir():
        shutil.copytree(source, destination, dirs_exist_ok=True)
    else:
        shutil.copy2(source, destination)


def ensure_polish_link(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    if "polish.css" in text:
        return
    marker = "</head>"
    if marker not in text:
        raise RuntimeError(f"Could not inject polish.css into {path}")
    text = text.replace(marker, '  <link rel="stylesheet" href="polish.css" />\n</head>', 1)
    path.write_text(text, encoding="utf-8")


def main() -> int:
    if SITE.exists():
        shutil.rmtree(SITE)
    SITE.mkdir(parents=True)

    # Preserve the original research console as a generated snapshot. It is now
    # embedded by the native dashboard.html wrapper instead of replacing the OS page.
    subprocess.run([sys.executable, str(EXPORT_SCRIPT)], cwd=ROOT, check=True)
    if not SHAREABLE.exists():
        raise FileNotFoundError(f"Shareable dashboard was not generated: {SHAREABLE}")

    if not SITE_SOURCE.exists():
        raise FileNotFoundError(f"Premium site source is missing: {SITE_SOURCE}")
    copy_if_exists(SITE_SOURCE, SITE)

    # Apply the shared product-polish/mobile layer to every native site page.
    for source_html in SITE_SOURCE.glob("*.html"):
        built_html = SITE / source_html.name
        if built_html.exists():
            ensure_polish_link(built_html)

    # Keep the legacy console accessible under a separate internal filename so the
    # native dashboard.html can provide Signal Bridge navigation and mobile escape.
    shutil.copy2(SHAREABLE, SITE / "research-dashboard.html")

    copy_if_exists(ROOT / "assets", SITE / "assets")
    for image in RESEARCH_IMAGES:
        copy_if_exists(image, SITE / "assets" / "research" / image.name)

    copy_if_exists(ROOT / "manifest.json", SITE / "manifest.json")
    copy_if_exists(ROOT / "metadata.json", SITE / "metadata.json")
    copy_if_exists(REPORT, SITE / "report.json")
    copy_if_exists(ROOT / "share" / "signal_bridge_report.json", SITE / "signal_bridge_report.json")

    # Prevent Jekyll processing from altering asset paths.
    (SITE / ".nojekyll").write_text("", encoding="utf-8")

    required = [
        SITE / "index.html",
        SITE / "trade-bible.html",
        SITE / "evidence.html",
        SITE / "signals.html",
        SITE / "signals.css",
        SITE / "strategies.html",
        SITE / "mason-orb.html",
        SITE / "strategy.css",
        SITE / "journal.html",
        SITE / "journal.css",
        SITE / "indicators.html",
        SITE / "reports.html",
        SITE / "dashboard.html",
        SITE / "research-dashboard.html",
        SITE / "polish.css",
        SITE / "assets" / "research" / "SPX500_2026-07-08_10-23-12.png",
        SITE / "assets" / "research" / "Tradezella-Summary-June-26-2026.png",
        SITE / "app.css",
        SITE / "report.json",
    ]
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        raise FileNotFoundError(f"Missing required Pages outputs: {missing}")

    print(f"Built Signal Bridge Premium OS Pages artifact at {SITE}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
