import json
import os
import sys
from datetime import datetime, timezone
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

INTEGRATIONS_ROOT = Path(__file__).resolve().parent
WORKSPACE_ROOT = INTEGRATIONS_ROOT.parents[2]
TV_ALERTS_PATH = INTEGRATIONS_ROOT / "tv_alerts.jsonl"

ALLOWED_EXTENSIONS = {".md", ".txt", ".csv", ".json", ".py", ".pine", ".html"}
MAX_PREVIEW_BYTES = 200_000
MAX_FILE_BYTES = 1_500_000

MODULE_FILE_RULES = {
    "strategy-center": [
        {"base": "trading_os", "glob": "*.md", "limit": 30},
        {"base": "strat", "glob": "*.md", "limit": 20},
        {"base": "trading_os/pine", "glob": "*.pine", "limit": 10},
    ],
    "backtests": [
        {"base": "strat", "glob": "*BACKTEST*.csv", "limit": 20},
        {"base": "trading_os/experiments", "glob": "*.csv", "limit": 20},
        {"base": "trading_os/experiments", "glob": "*.json", "limit": 20},
    ],
    "research-vault": [
        {"base": "trading_os/docs", "glob": "*.md", "limit": 50},
        {"base": "strat/research_texts", "glob": "*.md", "limit": 30},
        {"base": "strat", "glob": "*RESEARCH*.md", "limit": 30},
    ],
    "downloads": [
        {"base": "share", "glob": "*.html", "limit": 20},
        {"base": "share", "glob": "*.json", "limit": 20},
        {"base": "assets", "glob": "*.md", "limit": 20},
        {"base": "trading_os", "glob": "*CHECKLIST*.md", "limit": 20},
    ],
}

ALLOWED_LIBRARY_ROOTS = [
    (WORKSPACE_ROOT / "trading_os").resolve(),
    (WORKSPACE_ROOT / "strat").resolve(),
    (WORKSPACE_ROOT / "share").resolve(),
    (WORKSPACE_ROOT / "assets").resolve(),
]


def _is_under(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


def _to_relpath(path: Path) -> str:
    return path.resolve().relative_to(WORKSPACE_ROOT.resolve()).as_posix()


def _scan_module_files(module_id: str) -> list:
    rules = MODULE_FILE_RULES.get(module_id, [])
    items = []
    seen = set()

    for rule in rules:
        base_dir = (WORKSPACE_ROOT / rule["base"]).resolve()
        if not base_dir.exists() or not base_dir.is_dir():
            continue

        module_limit = int(rule.get("limit", 20))
        count = 0
        for file_path in sorted(base_dir.rglob(rule["glob"])):
            if count >= module_limit:
                break
            if not file_path.is_file():
                continue
            suffix = file_path.suffix.lower()
            if suffix not in ALLOWED_EXTENSIONS:
                continue
            size = file_path.stat().st_size
            if size > MAX_FILE_BYTES:
                continue

            rel = _to_relpath(file_path)
            if rel in seen:
                continue
            seen.add(rel)

            modified = datetime.fromtimestamp(file_path.stat().st_mtime, tz=timezone.utc).isoformat()
            items.append(
                {
                    "path": rel,
                    "name": file_path.name,
                    "size": size,
                    "modified": modified,
                    "extension": suffix,
                }
            )
            count += 1

    items.sort(key=lambda x: x.get("modified", ""), reverse=True)
    return items


def _build_library_catalog() -> dict:
    return {module_id: _scan_module_files(module_id) for module_id in MODULE_FILE_RULES}


def _load_library_file(rel_path: str) -> dict:
    rel_path = unquote(rel_path or "").strip()
    if not rel_path:
        raise ValueError("Missing file path")

    candidate = (WORKSPACE_ROOT / rel_path).resolve()
    workspace_resolved = WORKSPACE_ROOT.resolve()
    if not _is_under(candidate, workspace_resolved):
        raise ValueError("Path is outside workspace")

    if not any(_is_under(candidate, root) for root in ALLOWED_LIBRARY_ROOTS):
        raise ValueError("Path is not in an allowed library root")

    if not candidate.exists() or not candidate.is_file():
        raise FileNotFoundError("File not found")

    if candidate.suffix.lower() not in ALLOWED_EXTENSIONS:
        raise ValueError("File type is not supported")

    data = candidate.read_bytes()
    truncated = False
    if len(data) > MAX_PREVIEW_BYTES:
        data = data[:MAX_PREVIEW_BYTES]
        truncated = True

    content = data.decode("utf-8", errors="replace")
    return {
        "path": _to_relpath(candidate),
        "name": candidate.name,
        "size": candidate.stat().st_size,
        "truncated": truncated,
        "content": content,
    }


def _append_tv_alert(raw_payload: dict) -> dict:
    now_iso = datetime.now(timezone.utc).isoformat()
    alert = {
        "received_at": now_iso,
        "symbol": str(raw_payload.get("symbol") or "MES").upper(),
        "side": str(raw_payload.get("side") or raw_payload.get("action") or "WAIT").upper(),
        "price": raw_payload.get("price") or raw_payload.get("entry_price"),
        "event": raw_payload.get("event") or "alert",
        "note": raw_payload.get("note") or raw_payload.get("message") or "TradingView alert",
        "strategy": raw_payload.get("strategy") or "tv-webhook",
        "time": raw_payload.get("time") or raw_payload.get("timestamp") or now_iso,
        "raw": raw_payload,
    }

    TV_ALERTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with TV_ALERTS_PATH.open("a", encoding="utf-8") as fp:
        fp.write(json.dumps(alert, separators=(",", ":")) + "\n")

    return alert


def _read_recent_tv_alerts(limit: int = 100) -> list:
    if not TV_ALERTS_PATH.exists():
        return []

    entries = []
    with TV_ALERTS_PATH.open("r", encoding="utf-8") as fp:
        for line in fp:
            line = line.strip()
            if not line:
                continue
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                continue

    return entries[-limit:]


class DashboardHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(WORKSPACE_ROOT), **kwargs)

    def do_GET(self):
        parsed = urlparse(self.path)
        route = parsed.path

        if route in ("/report.json", "/trading_os/src/integrations/report.json"):
            report_path = INTEGRATIONS_ROOT / "report.json"
            if report_path.exists():
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(report_path.read_bytes())
            else:
                self.send_response(404)
                self.end_headers()
            return
        if route in ("/tv-alerts", "/trading_os/src/integrations/tv-alerts"):
            payload = {"alerts": _read_recent_tv_alerts(limit=200)}
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(payload).encode("utf-8"))
            return
        if route in ("/api/library", "/trading_os/src/integrations/api/library"):
            payload = {"modules": _build_library_catalog()}
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(payload).encode("utf-8"))
            return
        if route in ("/api/library/file", "/trading_os/src/integrations/api/library/file"):
            query = parse_qs(parsed.query or "")
            rel_path = query.get("path", [""])[0]
            try:
                payload = _load_library_file(rel_path)
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps(payload).encode("utf-8"))
            except FileNotFoundError as exc:
                self.send_response(404)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"ok": False, "error": str(exc)}).encode("utf-8"))
            except ValueError as exc:
                self.send_response(400)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"ok": False, "error": str(exc)}).encode("utf-8"))
            return
        super().do_GET()

    def do_POST(self):
        if self.path not in ("/tv-alert", "/trading_os/src/integrations/tv-alert"):
            self.send_response(404)
            self.end_headers()
            return

        content_length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(content_length) if content_length > 0 else b""

        try:
            payload = json.loads(body.decode("utf-8")) if body else {}
        except json.JSONDecodeError:
            self.send_response(400)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"ok": False, "error": "Invalid JSON payload"}).encode("utf-8"))
            return

        alert = _append_tv_alert(payload)
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({"ok": True, "alert": alert}).encode("utf-8"))


def main():
    port = int(os.getenv("DASHBOARD_PORT", "8000"))
    server = ThreadingHTTPServer(("127.0.0.1", port), DashboardHandler)
    print(f"Serving dashboard at http://127.0.0.1:{port}/index.html")
    server.serve_forever()


if __name__ == "__main__":
    main()
