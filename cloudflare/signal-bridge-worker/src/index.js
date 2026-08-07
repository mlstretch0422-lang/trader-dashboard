const TRADINGVIEW_IPS = new Set([
  "52.89.214.238",
  "34.212.75.30",
  "54.218.53.128",
  "52.32.178.7",
]);

const ALLOWED_SIDES = new Set(["LONG", "SHORT", "WAIT"]);
const ALLOWED_EVENTS = new Set(["ENTRY", "EXIT", "STOP", "TARGET", "ALERT", "TEST"]);
const ALLOWED_RESULTS = new Set(["WIN", "LOSS", "BE", "OPEN", "PASS", "NA"]);
const ALLOWED_VISIBILITY = new Set(["PRIVATE", "PUBLISHED"]);
const ALLOWED_REVIEW_STATUS = new Set(["RAW", "NORMALIZED", "REVIEWED"]);
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

function nullableText(value, maxLength) {
  const text = safeText(value, "", maxLength);
  return text || null;
}

function nullableNumber(value) {
  if (value === null || value === undefined || value === "") return null;
  const parsed = Number(value);
  if (!Number.isFinite(parsed)) throw new Error("invalid_number");
  return parsed;
}

function normalizeAlert(raw) {
  const side = safeText(raw.side, "WAIT", 16).toUpperCase();
  const event = safeText(raw.event, "ALERT", 24).replaceAll("_", " ").toUpperCase();
  const symbol = safeText(raw.symbol, "MES", 32).toUpperCase();
  const strategy = safeText(raw.strategy, "TradingView", 96);
  const note = safeText(raw.note, "TradingView alert", 320);
  const time = safeText(raw.time, "", 96);
  const price = raw.price === null || raw.price === undefined ? null : safeText(raw.price, "", 48);

  if (!ALLOWED_SIDES.has(side)) throw new Error("invalid_side");
  if (!ALLOWED_EVENTS.has(event)) throw new Error("invalid_event");

  return { symbol, side, event, price, strategy, note, time };
}

function normalizeJournal(raw) {
  const rawText = safeText(raw.raw_text ?? raw.text ?? raw.note, "", 4000);
  if (!rawText) throw new Error("journal_text_required");

  const sideText = safeText(raw.side, "", 16).toUpperCase();
  if (sideText && !ALLOWED_SIDES.has(sideText)) throw new Error("invalid_side");

  const result = safeText(raw.result, "NA", 16).toUpperCase();
  if (!ALLOWED_RESULTS.has(result)) throw new Error("invalid_result");

  const visibility = safeText(raw.visibility, "PRIVATE", 16).toUpperCase();
  if (!ALLOWED_VISIBILITY.has(visibility)) throw new Error("invalid_visibility");

  const reviewStatus = safeText(raw.review_status, "RAW", 16).toUpperCase();
  if (!ALLOWED_REVIEW_STATUS.has(reviewStatus)) throw new Error("invalid_review_status");

  let tags = raw.tags ?? [];
  if (typeof tags === "string") {
    tags = tags.split(",").map((tag) => tag.trim()).filter(Boolean);
  }
  if (!Array.isArray(tags)) throw new Error("invalid_tags");
  tags = tags.slice(0, 20).map((tag) => safeText(tag, "", 40)).filter(Boolean);

  return {
    journal_time: nullableText(raw.journal_time ?? raw.time, 96),
    symbol: nullableText(raw.symbol, 32)?.toUpperCase() ?? null,
    side: sideText || null,
    setup: nullableText(raw.setup, 96),
    strategy: nullableText(raw.strategy, 96),
    title: nullableText(raw.title, 160),
    raw_text: rawText,
    summary: nullableText(raw.summary, 600),
    result,
    pnl: nullableNumber(raw.pnl),
    rr: nullableNumber(raw.rr),
    tags: JSON.stringify(tags),
    source: safeText(raw.source, "manual", 48).toLowerCase(),
    source_ref: nullableText(raw.source_ref, 512),
    signal_event_id: nullableText(raw.signal_event_id, 64),
    image_url: nullableText(raw.image_url, 1024),
    visibility,
    review_status: reviewStatus,
  };
}

function buildDiscordMessage(alert) {
  const lines = [
    `SIGNAL BRIDGE | ${alert.event}`,
    `${alert.symbol} | ${alert.side}`,
  ];

  if (alert.price) lines.push(`Price: ${alert.price}`);
  lines.push(`Strategy: ${alert.strategy}`);
  lines.push(`Note: ${alert.note}`);
  if (alert.time) lines.push(`Time: ${alert.time}`);

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
        "user-agent": "SignalBridgeWorker/1.2",
      },
      body: JSON.stringify(buildDiscordMessage(alert)),
    });

    if (!response.ok) console.error(`Signal Bridge Worker: Discord returned HTTP ${response.status}`);
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

async function persistJournal(record, env) {
  if (!env.DB) throw new Error("journal_storage_not_configured");

  await env.DB.prepare(
    `INSERT INTO journal_entries (
      id, created_at, journal_time, symbol, side, setup, strategy, title,
      raw_text, summary, result, pnl, rr, tags, source, source_ref,
      signal_event_id, image_url, visibility, review_status
    ) VALUES (
      ?1, ?2, ?3, ?4, ?5, ?6, ?7, ?8, ?9, ?10,
      ?11, ?12, ?13, ?14, ?15, ?16, ?17, ?18, ?19, ?20
    )`,
  )
    .bind(
      record.id,
      record.created_at,
      record.journal_time,
      record.symbol,
      record.side,
      record.setup,
      record.strategy,
      record.title,
      record.raw_text,
      record.summary,
      record.result,
      record.pnl,
      record.rr,
      record.tags,
      record.source,
      record.source_ref,
      record.signal_event_id,
      record.image_url,
      record.visibility,
      record.review_status,
    )
    .run();
}

async function listEvents(url, env) {
  if (!env.DB) return publicJson({ ok: false, error: "history_storage_not_configured" }, 503);

  const rawLimit = Number.parseInt(url.searchParams.get("limit") || "25", 10);
  const limit = Number.isFinite(rawLimit) ? Math.min(Math.max(rawLimit, 1), MAX_HISTORY_LIMIT) : 25;
  const includeTests = url.searchParams.get("include_tests") === "1";
  const requestedSide = safeText(url.searchParams.get("side"), "", 16).toUpperCase();
  const requestedEvent = safeText(url.searchParams.get("event"), "", 24).replaceAll("_", " ").toUpperCase();

  if (requestedSide && !ALLOWED_SIDES.has(requestedSide)) return publicJson({ ok: false, error: "invalid_side" }, 400);
  if (requestedEvent && !ALLOWED_EVENTS.has(requestedEvent)) return publicJson({ ok: false, error: "invalid_event" }, 400);

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
    return publicJson({ ok: true, count: events.length, include_tests: includeTests, events });
  } catch (error) {
    console.error(`Signal Bridge Worker: history query failed: ${error?.message || "D1_ERROR"}`);
    return publicJson({ ok: false, error: "history_query_failed" }, 500);
  }
}

async function listPublishedJournal(url, env) {
  if (!env.DB) return publicJson({ ok: false, error: "journal_storage_not_configured" }, 503);

  const rawLimit = Number.parseInt(url.searchParams.get("limit") || "25", 10);
  const limit = Number.isFinite(rawLimit) ? Math.min(Math.max(rawLimit, 1), MAX_HISTORY_LIMIT) : 25;
  const symbol = safeText(url.searchParams.get("symbol"), "", 32).toUpperCase();
  const resultFilter = safeText(url.searchParams.get("result"), "", 16).toUpperCase();
  const setup = safeText(url.searchParams.get("setup"), "", 96);

  if (resultFilter && !ALLOWED_RESULTS.has(resultFilter)) {
    return publicJson({ ok: false, error: "invalid_result" }, 400);
  }

  const where = ["visibility = ?1"];
  const values = ["PUBLISHED"];
  if (symbol) {
    where.push(`symbol = ?${values.length + 1}`);
    values.push(symbol);
  }
  if (resultFilter) {
    where.push(`result = ?${values.length + 1}`);
    values.push(resultFilter);
  }
  if (setup) {
    where.push(`setup = ?${values.length + 1}`);
    values.push(setup);
  }

  values.push(limit);
  const query = `
    SELECT id, created_at, journal_time, symbol, side, setup, strategy, title,
           raw_text, summary, result, pnl, rr, tags, source, signal_event_id,
           image_url, review_status
    FROM journal_entries
    WHERE ${where.join(" AND ")}
    ORDER BY COALESCE(journal_time, created_at) DESC
    LIMIT ?${values.length}
  `;

  try {
    const result = await env.DB.prepare(query).bind(...values).run();
    const entries = (Array.isArray(result.results) ? result.results : []).map((entry) => ({
      ...entry,
      tags: (() => {
        try { return JSON.parse(entry.tags || "[]"); } catch { return []; }
      })(),
    }));
    return publicJson({ ok: true, count: entries.length, entries });
  } catch (error) {
    console.error(`Signal Bridge Worker: journal query failed: ${error?.message || "D1_ERROR"}`);
    return publicJson({ ok: false, error: "journal_query_failed" }, 500);
  }
}

async function readJson(request) {
  const contentType = request.headers.get("content-type") || "";
  if (!contentType.toLowerCase().includes("application/json")) throw new Error("content_type_must_be_json");

  const contentLength = Number(request.headers.get("content-length") || 0);
  if (contentLength > MAX_BODY_BYTES) throw new Error("body_too_large");

  const text = await request.text();
  if (new TextEncoder().encode(text).byteLength > MAX_BODY_BYTES) throw new Error("body_too_large");

  return JSON.parse(text);
}

function bearerToken(request) {
  const auth = request.headers.get("authorization") || "";
  return auth.startsWith("Bearer ") ? auth.slice(7) : "";
}

function requireBearer(request, expected) {
  return Boolean(expected) && bearerToken(request) === expected;
}

export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);

    if (request.method === "GET" && url.pathname === "/health") {
      return publicJson({
        ok: true,
        service: "signal-bridge-worker",
        version: "1.2.0",
        history_storage: Boolean(env.DB),
        journal_storage: Boolean(env.DB),
        journal_ingest_configured: Boolean(env.JOURNAL_INGEST_TOKEN),
      });
    }

    if (request.method === "GET" && url.pathname === "/events") return listEvents(url, env);
    if (request.method === "GET" && url.pathname === "/journal") return listPublishedJournal(url, env);

    if (request.method !== "POST") return responseJson({ ok: false, error: "not_found" }, 404);

    if (url.pathname === "/journal") {
      if (!env.JOURNAL_INGEST_TOKEN) return responseJson({ ok: false, error: "journal_ingest_not_configured" }, 503);
      if (!requireBearer(request, env.JOURNAL_INGEST_TOKEN)) return responseJson({ ok: false, error: "unauthorized" }, 401);

      try {
        const raw = await readJson(request);
        const entry = normalizeJournal(raw);
        const record = {
          id: crypto.randomUUID(),
          created_at: new Date().toISOString(),
          ...entry,
        };
        await persistJournal(record, env);
        return responseJson({
          ok: true,
          accepted: true,
          journal_id: record.id,
          visibility: record.visibility,
          review_status: record.review_status,
        }, 201);
      } catch (error) {
        const reason = error instanceof SyntaxError ? "invalid_json" : String(error?.message || "invalid_request");
        const status = reason === "body_too_large" ? 413 : reason === "journal_storage_not_configured" ? 503 : 400;
        return responseJson({ ok: false, error: reason }, status);
      }
    }

    const isTradingViewRoute = url.pathname === "/tv-alert";
    const isTestRoute = url.pathname === "/test";
    if (!isTradingViewRoute && !isTestRoute) return responseJson({ ok: false, error: "not_found" }, 404);

    if (isTradingViewRoute) {
      const sourceIp = request.headers.get("cf-connecting-ip") || "";
      if (!TRADINGVIEW_IPS.has(sourceIp)) return responseJson({ ok: false, error: "source_not_allowed" }, 403);
    } else if (!requireBearer(request, env.SIGNAL_BRIDGE_TEST_TOKEN)) {
      return responseJson({ ok: false, error: "unauthorized" }, 401);
    }

    let alert;
    try {
      const raw = await readJson(request);
      alert = normalizeAlert(raw);
      if (isTestRoute) alert.event = "TEST";
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

    return responseJson({
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
    }, 202);
  },
};
