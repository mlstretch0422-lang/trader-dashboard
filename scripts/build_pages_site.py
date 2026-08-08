#!/usr/bin/env python3
"""Build the Signal Bridge static artifact for GitHub Pages."""

from __future__ import annotations

import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "_site"
SITE_SOURCE = ROOT / "site"
REPORT = ROOT / "trading_os" / "src" / "integrations" / "report.json"
MEMBER_URL = "https://signal-bridge-webhook.airy-iris.workers.dev/member"

RESEARCH_IMAGE_MAP = [
    (ROOT / "SPX500_2026-07-08_10-23-12.png", "SPX500_2026-07-08_10-23-12.png"),
    (ROOT / "Tradezella-Summary-June-26-2026.png", "Tradezella-Summary-June-26-2026.png"),
    (ROOT / "helper sc.png", "helper-panel-01.png"),
    (ROOT / "helper sc 2.png", "helper-panel-02.png"),
    (ROOT / "strat" / "Trade Stratagey" / "MES1!_2026-03-21_12-26-49.png", "mes-study-01.png"),
    (ROOT / "strat" / "Trade Stratagey" / "MES1!_2026-03-21_12-51-44.png", "mes-study-02.png"),
    (ROOT / "strat" / "Trade Stratagey" / "MES1!_2026-03-21_13-18-29.png", "mes-study-03.png"),
    (ROOT / "strat" / "Trade Stratagey" / "MES1!_2026-03-21_13-19-13.png", "mes-study-04.png"),
]

NAV_ITEMS = [
    ("index.html", "Home"),
    ("signals.html", "Signals"),
    ("strategies.html", "Strategies"),
    ("indicators.html", "Indicators"),
    ("journal.html", "Journal"),
    ("mason.html", "Mason"),
    (MEMBER_URL, "Member"),
]

MASON_SECTION_PAGES = {"mason.html", "mason-orb.html", "trade-bible.html", "evidence.html"}

LEGAL_NOTE = (
    '<div class="legal-disclaimer"><div class="shell">'
    'Signal Bridge provides trading research, education, software tools, and market information. '
    'Nothing on this site is financial advice or a guarantee of future results. Trading involves risk.'
    '</div></div>'
)


def copy_if_exists(source: Path, destination: Path) -> None:
    if not source.exists():
        return
    destination.parent.mkdir(parents=True, exist_ok=True)
    if source.is_dir():
        shutil.copytree(source, destination, dirs_exist_ok=True)
    else:
        shutil.copy2(source, destination)


def apply_native_shell(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    if "polish.css" not in text:
        marker = "</head>"
        if marker not in text:
            raise RuntimeError(f"Could not inject polish.css into {path}")
        text = text.replace(marker, '  <link rel="stylesheet" href="polish.css" />\n</head>', 1)

    links = []
    for href, label in NAV_ITEMS:
        if href == "mason.html":
            is_active = path.name in MASON_SECTION_PAGES
        elif href.startswith("http"):
            is_active = False
        else:
            is_active = path.name == href
        active = ' class="active"' if is_active else ""
        links.append(f'        <a{active} href="{href}">{label}</a>')
    nav_html = '<nav class="nav" aria-label="Main navigation">\n' + "\n".join(links) + "\n      </nav>"

    text, count = re.subn(r'<nav class="nav"(?:\s+aria-label="[^"]*")?>.*?</nav>', nav_html, text, count=1, flags=re.DOTALL)
    # Redirect compatibility pages intentionally have no navigation.
    if count == 0 and path.name not in {"dashboard.html", "reports.html"}:
        raise RuntimeError(f"Could not normalize navigation in {path}")

    mason_breadcrumbs = {
        "mason-orb.html": '<div class="breadcrumb"><a href="index.html">Signal Bridge</a> / <a href="mason.html">Mason</a> / Mason ORB</div>',
        "trade-bible.html": '<div class="breadcrumb"><a href="index.html">Signal Bridge</a> / <a href="mason.html">Mason</a> / Trade Bible</div>',
        "evidence.html": '<div class="breadcrumb"><a href="index.html">Signal Bridge</a> / <a href="mason.html">Mason</a> / Research &amp; Evidence</div>',
    }
    if path.name in mason_breadcrumbs:
        text, breadcrumb_count = re.subn(r'<div class="breadcrumb">.*?</div>', mason_breadcrumbs[path.name], text, count=1, flags=re.DOTALL)
        if breadcrumb_count == 0:
            raise RuntimeError(f"Could not normalize Mason breadcrumb in {path}")

    if "legal-disclaimer" not in text and "</body>" in text:
        text = text.replace("</body>", f"  {LEGAL_NOTE}\n</body>", 1)

    path.write_text(text, encoding="utf-8")


def main() -> int:
    if SITE.exists():
        shutil.rmtree(SITE)
    SITE.mkdir(parents=True)

    if not SITE_SOURCE.exists():
        raise FileNotFoundError(f"Premium site source is missing: {SITE_SOURCE}")
    copy_if_exists(SITE_SOURCE, SITE)

    for source_html in SITE_SOURCE.glob("*.html"):
        built_html = SITE / source_html.name
        if built_html.exists():
            apply_native_shell(built_html)

    copy_if_exists(ROOT / "assets", SITE / "assets")
    for source, public_name in RESEARCH_IMAGE_MAP:
        copy_if_exists(source, SITE / "assets" / "research" / public_name)

    copy_if_exists(ROOT / "manifest.json", SITE / "manifest.json")
    copy_if_exists(ROOT / "metadata.json", SITE / "metadata.json")
    copy_if_exists(REPORT, SITE / "report.json")
    copy_if_exists(ROOT / "share" / "signal_bridge_report.json", SITE / "signal_bridge_report.json")

    (SITE / ".nojekyll").write_text("", encoding="utf-8")

    required = [
        SITE / "index.html",
        SITE / "mason.html",
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
        SITE / "research.css",
        SITE / "polish.css",
        SITE / "assets" / "research" / "mes-study-01.png",
        SITE / "assets" / "research" / "mes-study-02.png",
        SITE / "assets" / "research" / "mes-study-03.png",
        SITE / "assets" / "research" / "mes-study-04.png",
        SITE / "assets" / "research" / "helper-panel-01.png",
        SITE / "assets" / "research" / "helper-panel-02.png",
        SITE / "app.css",
        SITE / "report.json",
    ]
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        raise FileNotFoundError(f"Missing required Pages outputs: {missing}")

    print(f"Built Signal Bridge Pages artifact at {SITE}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
