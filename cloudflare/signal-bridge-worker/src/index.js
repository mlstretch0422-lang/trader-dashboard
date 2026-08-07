const TRADINGVIEW_IPS = new Set([
  "52.89.214.238",
  "34.212.75.30",
  "54.218.53.128",
  "52.32.178.7",
]);

const ALLOWED_SIDES = new Set(["LONG", "SHORT", "WAIT"]);
const ALLOWED_EVENTS = new Set(["ENTRY", "EXIT", "STOP", "TARGET", "ALERT", "TEST"]);
const MAX_BODY_BYTES = 16 * 1024;
const MAX_HISTORY_LIMIT = 100;

function responseJson(body, status = 200, extraHeaders = {}) {
  return new Response(JSON.stringify(body), {
    status,
    headers: {
      "content-type": "application/json; charset=utf-8",
      "cache-control": "no-store",
      ...extraHeaders,
    },
  });
}

function publicJson(body, status = 200) {
  return responseJson(body, status, {
    "access-control-allow-origin": "*",
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
        "user-agent": "SignalBridgeWorker/1.1",
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

async function persistEvent(record, env) {
  if (!env.DB) {
    console.warn("Signal Bridge Worker: DB binding is not configured; event history skipped");
    return;
  }

  try {
    await env.DB.prepare(
      `INSERT INTO signal_events (
        id, received_at, alert_time, symbol, side, event, price, strategy, note, source
      ) VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7, ?8, ?9, ?10)`,
    )
      .bind(
        record.id,
        record.received_at,
        record.time || null,
        record.symbol,
        record.side,
        record.event,
        record.price,
        record.strategy,
        record.note,
        record.source,
      )
      .run();
  } catch (error) {
    console.error(`Signal Bridge Worker: event persistence failed: ${error?.message || "D1_ERROR"}`);
  }
}

async function listEvents(url, env) {
  if (!env.DB) {
    return publicJson({ ok: false, error: "history_storage_not_configured" }, 503);
  }

  const rawLimit = Number.parseInt(url.searchParams.get("limit") || "25", 10);
  const limit = Number.isFinite(rawLimit) ? Math.min(Math.max(rawLimit, 1), MAX_HISTORY_LIMIT) : 25;
  const includeTests = url.searchParams.get("include_tests") === "1";
  const requestedSide = safeText(url.searchParams.get("side"), "", 16).toUpperCase();
  const requestedEvent = safeText(url.searchParams.get("event"), "", 24).replaceAll("_", " ").toUpperCase();

  if (requestedSide && !ALLOWED_SIDES.has(requestedSide)) {
    return publicJson({ ok: false, error: "invalid_side" }, 400);
  }
  if (requestedEvent && !ALLOWED_EVENTS.has(requestedEvent)) {
    return publicJson({ ok: false, error: "invalid_event" }, 400);
  }

  const where = [];
  const values = [];
  if (!includeTests) {
    where.push(`event <> ?${values.length + 1}`);
    values.push("TEST");
  }
  if (requestedSide) {
    where.push(`side = ?${values.length + 1}`);
    values.push(requestedSide);
  }
  if (requestedEvent) {
    where.push(`event = ?${values.length + 1}`);
    values.push(requestedEvent);
  }

  values.push(limit);
  const limitToken = `?${values.length}`;
  const whereClause = where.length ? `WHERE ${where.join(" AND ")}` : "";
  const query = `
    SELECT id, received_at, alert_time, symbol, side, event, price, strategy, note, source
    FROM signal_events
    ${whereClause}
    ORDER BY received_at DESC
    LIMIT ${limitToken}
  `;

  try {
    const result = await env.DB.prepare(query).bind(...values).run();
    const events = Array.isArray(result.results) ? result.results : [];
    return publicJson({
      ok: true,
      count: events.length,
      include_tests: includeTests,
      events,
    });
  } catch (error) {
    console.error(`Signal Bridge Worker: history query failed: ${error?.message || "D1_ERROR"}`);
    return publicJson({ ok: false, error: "history_query_failed" }, 500);
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
      return publicJson({
        ok: true,
        service: "signal-bridge-worker",
        version: "1.1.0",
        history_storage: Boolean(env.DB),
      });
    }

    if (request.method === "GET" && url.pathname === "/events") {
      return listEvents(url, env);
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

    const record = {
      id: crypto.randomUUID(),
      received_at: new Date().toISOString(),
      source: isTradingViewRoute ? "tradingview" : "authenticated-test",
      ...alert,
    };

    ctx.waitUntil(Promise.allSettled([
      postDiscord(alert, env),
      persistEvent(record, env),
    ]));

    return responseJson(
      {
        ok: true,
        accepted: true,
        event_id: record.id,
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
