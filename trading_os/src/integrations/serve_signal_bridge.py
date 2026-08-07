"""Signal Bridge dashboard server with authenticated TradingView -> Discord forwarding."""

import hmac
import json
import os
from http.server import ThreadingHTTPServer

from alert_bridge import send_tradingview_alert
from serve_dashboard import DashboardHandler, _append_tv_alert


class SignalBridgeHandler(DashboardHandler):
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
            self._send_json(400, {"ok": False, "error": "Invalid JSON payload"})
            return

        expected_secret = os.getenv("TV_WEBHOOK_SECRET", "").strip()
        supplied_secret = str(payload.get("secret") or "")
        if expected_secret and not hmac.compare_digest(supplied_secret, expected_secret):
            self._send_json(401, {"ok": False, "error": "Unauthorized webhook"})
            return

        # Never persist the webhook authentication secret in alert history.
        sanitized = dict(payload)
        sanitized.pop("secret", None)

        alert = _append_tv_alert(sanitized)
        discord_result = send_tradingview_alert(alert)
        self._send_json(
            200,
            {
                "ok": True,
                "alert": alert,
                "discord": discord_result,
            },
        )

    def _send_json(self, status: int, payload: dict) -> None:
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(payload).encode("utf-8"))


def main():
    port = int(os.getenv("DASHBOARD_PORT", "8000"))
    server = ThreadingHTTPServer(("127.0.0.1", port), SignalBridgeHandler)
    print(f"Signal Bridge dashboard: http://127.0.0.1:{port}/index.html")
    print(f"TradingView webhook: http://127.0.0.1:{port}/tv-alert")
    server.serve_forever()


if __name__ == "__main__":
    main()
