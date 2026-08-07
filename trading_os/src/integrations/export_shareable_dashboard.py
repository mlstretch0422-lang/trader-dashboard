import json
from datetime import datetime, timezone
from pathlib import Path


WORKSPACE_ROOT = Path(__file__).resolve().parents[3]
INDEX_PATH = WORKSPACE_ROOT / "index.html"
REPORT_PATH = WORKSPACE_ROOT / "trading_os" / "src" / "integrations" / "report.json"
SHARE_DIR = WORKSPACE_ROOT / "share"
SHARE_HTML_PATH = SHARE_DIR / "signal_bridge_premium_shareable.html"
SHARE_REPORT_PATH = SHARE_DIR / "signal_bridge_report.json"


def build_shareable_html(index_html: str, report_payload: dict) -> str:
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    embed_script = (
        "<script>\n"
        f"window.__EMBEDDED_REPORT__ = {json.dumps(report_payload, separators=(',', ':'))};\n"
        f"window.__EMBEDDED_SOURCE__ = 'snapshot generated {timestamp}';\n"
        "</script>\n"
    )

    marker = "  <script>"
    if marker not in index_html:
        raise RuntimeError("Could not find script marker in index.html")

    return index_html.replace(marker, embed_script + marker, 1)


def main() -> None:
    if not INDEX_PATH.exists():
        raise FileNotFoundError(f"Missing index file: {INDEX_PATH}")
    if not REPORT_PATH.exists():
        raise FileNotFoundError(f"Missing report file: {REPORT_PATH}")

    index_html = INDEX_PATH.read_text(encoding="utf-8")
    report_payload = json.loads(REPORT_PATH.read_text(encoding="utf-8"))

    shareable_html = build_shareable_html(index_html, report_payload)

    SHARE_DIR.mkdir(parents=True, exist_ok=True)
    SHARE_HTML_PATH.write_text(shareable_html, encoding="utf-8")
    SHARE_REPORT_PATH.write_text(json.dumps(report_payload, indent=2), encoding="utf-8")

    print(f"Wrote shareable dashboard: {SHARE_HTML_PATH}")
    print(f"Wrote share snapshot data: {SHARE_REPORT_PATH}")


if __name__ == "__main__":
    main()
