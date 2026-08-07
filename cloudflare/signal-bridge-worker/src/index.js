const TRADINGVIEW_IPS = new Set([
  "52.89.214.238",
  "34.212.75.30",
  "54.218.53.128",
  "52.32.178.7",
]);

const ALLOWED_SIDES = new Set(["LONG", "SHORT", "WAIT"]);
const ALLOWED_EVENTS = new Set(["ENTRY", "EXIT", "STOP", "TARGET", "ALERT", "TEST"]);
const MAX_BODY_BYTES = 16 * 1024;

function responseJson(body, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: {
      "content-type": "application/json; charset=utf-8",
      "cache-control": "no-store",
    },
  });
}

function safeText(value, fallback, maxLength) {
  const text = String(value ?? fallback ?? "").trim();
  return text.slice(0, maxLength);
}

function normalizeAlert(raw) {
  const side = safeText(raw.side, "WAIT", 16).toUpperCase();
  const event = safeText(raw.event, "ALERT", 24).replaceAll("_", " ").toUpperCase();
  const symbol = safeText(raw.symbol, "MES", 32).toUpperCase();
  const strategy = safeText(raw.strategy, "TradingView", 96);
  const note = safeText(raw.note, "TradingView alert", 320);
  const time = safeText(raw.time, "", 96);
  const price = raw.price === null || raw.price === undefined ? null : safeText(raw.price, "", 48);

  if (!ALLOWED_SIDES.has(side)) {
    throw new Error("invalid_side");
  }
  if (!ALLOWED_EVENTS.has(event)) {
    throw new Error("invalid_event");
  }

  return { symbol, side, event, price, strategy, note, time };
}

function buildDiscordMessage(alert) {
  const lines = [
    `SIGNAL BRIDGE | ${alert.event}`,
    `${alert.symbol} | ${alert.side}`,
  ];

  if (alert.price) {
    lines.push(`Price: ${alert.price}`);
  }

  lines.push(`Strategy: ${alert.strategy}`);
  lines.push(`Note: ${alert.note}`);

  if (alert.time) {
    lines.push(`Time: ${alert.time}`);
  }

  return { content: lines.join("\n") };
}

async function postDiscord(alert, env) {
  if (!env.DISCORD_WEBHOOK_URL) {
    console.error("Signal Bridge Worker: DISCORD_WEBHOOK_URL is not configured");
    return;
  }

  try {
    const response = await fetch(env.DISCORD_WEBHOOK_URL, {
      method: "POST",
      headers: {
        "content-type": "application/json",
        "user-agent": "SignalBridgeWorker/1.0",
      },
      body: JSON.stringify(buildDiscordMessage(alert)),
    });

    if (!response.ok) {
      console.error(`Signal Bridge Worker: Discord returned HTTP ${response.status}`);
    }
  } catch (error) {
    console.error(`Signal Bridge Worker: Discord delivery failed: ${error?.name || "Error"}`);
  }
}

async function readJson(request) {
  const contentType = request.headers.get("content-type") || "";
  if (!contentType.toLowerCase().includes("application/json")) {
    throw new Error("content_type_must_be_json");
  }

  const contentLength = Number(request.headers.get("content-length") || 0);
  if (contentLength > MAX_BODY_BYTES) {
    throw new Error("body_too_large");
  }

  const text = await request.text();
  if (new TextEncoder().encode(text).byteLength > MAX_BODY_BYTES) {
    throw new Error("body_too_large");
  }

  return JSON.parse(text);
}

function bearerToken(request) {
  const auth = request.headers.get("authorization") || "";
  return auth.startsWith("Bearer ") ? auth.slice(7) : "";
}

export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);

    if (request.method === "GET" && url.pathname === "/health") {
      return responseJson({
        ok: true,
        service: "signal-bridge-worker",
        version: "1.0.0",
      });
    }

    if (request.method !== "POST") {
      return responseJson({ ok: false, error: "not_found" }, 404);
    }

    const isTradingViewRoute = url.pathname === "/tv-alert";
    const isTestRoute = url.pathname === "/test";
    if (!isTradingViewRoute && !isTestRoute) {
      return responseJson({ ok: false, error: "not_found" }, 404);
    }

    if (isTradingViewRoute) {
      const sourceIp = request.headers.get("cf-connecting-ip") || "";
      if (!TRADINGVIEW_IPS.has(sourceIp)) {
        return responseJson({ ok: false, error: "source_not_allowed" }, 403);
      }
    } else {
      const supplied = bearerToken(request);
      if (!env.SIGNAL_BRIDGE_TEST_TOKEN || supplied !== env.SIGNAL_BRIDGE_TEST_TOKEN) {
        return responseJson({ ok: false, error: "unauthorized" }, 401);
      }
    }

    let alert;
    try {
      const raw = await readJson(request);
      alert = normalizeAlert(raw);
      if (isTestRoute) {
        alert.event = "TEST";
      }
    } catch (error) {
      const reason = error instanceof SyntaxError ? "invalid_json" : String(error?.message || "invalid_request");
      const status = reason === "body_too_large" ? 413 : 400;
      return responseJson({ ok: false, error: reason }, status);
    }

    ctx.waitUntil(postDiscord(alert, env));

    return responseJson(
      {
        ok: true,
        accepted: true,
        alert: {
          symbol: alert.symbol,
          side: alert.side,
          event: alert.event,
          price: alert.price,
          strategy: alert.strategy,
          note: alert.note,
          time: alert.time,
        },
      },
      202,
    );
  },
};
