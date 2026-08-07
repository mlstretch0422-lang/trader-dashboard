const TRADINGVIEW_IPS = new Set([
  "52.89.214.238",
  "34.212.75.30",
  "54.218.53.128",
  "52.32.178.7",
]);

const ALLOWED_STAGES = new Set([
  "PREMARKET",
  "ORB_FORMED",
  "PREOPEN",
  "OPEN_SNAPSHOT",
  "SETUP",
  "WAIT",
  "SESSION_CLOSE",
  "TEST",
]);
const ALLOWED_SIDES = new Set(["LONG", "SHORT", "WAIT"]);
const MAX_BODY_BYTES = 16 * 1024;
const MAX_LIMIT = 100;

function publicJson(body, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: {
      "content-type": "application/json; charset=utf-8",
      "cache-control": "no-store",
      "access-control-allow-origin": "*",
    },
  });
}

function safeText(value, fallback = "", maxLength = 160) {
  return String(value ?? fallback ?? "").trim().slice(0, maxLength);
}

function nullableText(value, maxLength = 160) {
  const text = safeText(value, "", maxLength);
  return text || null;
}

function nullableNumber(value) {
  if (value === null || value === undefined || value === "") return null;
  const parsed = Number(value);
  if (!Number.isFinite(parsed)) throw new Error("invalid_number");
  return parsed;
}

function nyDate(date = new Date()) {
  const parts = new Intl.DateTimeFormat("en-US", {
    timeZone: "America/New_York",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  }).formatToParts(date);
  const map = Object.fromEntries(parts.map((part) => [part.type, part.value]));
  return `${map.year}-${map.month}-${map.day}`;
}

function normalizeSessionDate(value) {
  const explicit = safeText(value, "", 10);
  if (!explicit) return nyDate();
  if (!/^\d{4}-\d{2}-\d{2}$/.test(explicit)) throw new Error("invalid_session_date");
  return explicit;
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

function normalizeSessionEvent(raw, forceTest = false) {
  const stage = forceTest
    ? "TEST"
    : safeText(raw.stage ?? raw.event, "", 32).replaceAll(" ", "_").toUpperCase();
  if (!ALLOWED_STAGES.has(stage)) throw new Error("invalid_session_stage");

  const sideText = safeText(raw.side, "", 16).toUpperCase();
  if (sideText && !ALLOWED_SIDES.has(sideText)) throw new Error("invalid_side");

  const orb = raw.orb && typeof raw.orb === "object" ? raw.orb : {};
  const orbHigh = nullableNumber(raw.orb_high ?? orb.high);
  const orbLow = nullableNumber(raw.orb_low ?? orb.low);
  let orbMid = nullableNumber(raw.orb_mid ?? orb.mid);
  let rangePoints = nullableNumber(raw.range_points ?? orb.range_points ?? orb.range);
  if (orbMid === null && orbHigh !== null && orbLow !== null) orbMid = (orbHigh + orbLow) / 2;
  if (rangePoints === null && orbHigh !== null && orbLow !== null) rangePoints = Math.abs(orbHigh - orbLow);

  const eventTime = nullableText(raw.time ?? raw.event_time, 96);
  return {
    session_date: normalizeSessionDate(raw.session_date),
    event_time: eventTime,
    symbol: safeText(raw.symbol, "MES", 32).toUpperCase(),
    stage,
    side: sideText || null,
    price: nullableNumber(raw.price),
    strategy: safeText(raw.strategy, "Signal Bridge Session", 96),
    note: safeText(raw.note, stage.replaceAll("_", " "), 500),
    timeframe: nullableText(raw.timeframe, 24),
    orb_high: orbHigh,
    orb_low: orbLow,
    orb_mid: orbMid,
    range_points: rangePoints,
    bias: nullableText(raw.bias, 48),
    setup: nullableText(raw.setup, 96),
    target: nullableText(raw.target, 160),
    outcome: nullableText(raw.outcome, 160),
    payload_json: JSON.stringify(raw),
  };
}

async function persistSessionEvent(record, env) {
  if (!env.DB) throw new Error("session_storage_not_configured");
  await env.DB.prepare(
    `INSERT INTO session_events (
      id, received_at, event_time, session_date, symbol, stage, side, price,
      strategy, note, timeframe, orb_high, orb_low, orb_mid, range_points,
      bias, setup, target, outcome, payload_json, source
    ) VALUES (
      ?1, ?2, ?3, ?4, ?5, ?6, ?7, ?8, ?9, ?10, ?11,
      ?12, ?13, ?14, ?15, ?16, ?17, ?18, ?19, ?20, ?21
    )`,
  ).bind(
    record.id,
    record.received_at,
    record.event_time,
    record.session_date,
    record.symbol,
    record.stage,
    record.side,
    record.price,
    record.strategy,
    record.note,
    record.timeframe,
    record.orb_high,
    record.orb_low,
    record.orb_mid,
    record.range_points,
    record.bias,
    record.setup,
    record.target,
    record.outcome,
    record.payload_json,
    record.source,
  ).run();
}

function formatNumber(value) {
  if (value === null || value === undefined) return null;
  const number = Number(value);
  if (!Number.isFinite(number)) return String(value);
  return Number.isInteger(number) ? String(number) : number.toFixed(2).replace(/0+$/, "").replace(/\.$/, "");
}

function buildDiscordMessage(record) {
  const title = record.stage.replaceAll("_", " ");
  const lines = [`**SIGNAL BRIDGE | ${title}**`, `${record.symbol} · ${record.session_date}`];

  if (record.stage === "ORB_FORMED") {
    const values = [
      record.orb_high !== null ? `H ${formatNumber(record.orb_high)}` : null,
      record.orb_low !== null ? `L ${formatNumber(record.orb_low)}` : null,
      record.orb_mid !== null ? `M ${formatNumber(record.orb_mid)}` : null,
      record.range_points !== null ? `${formatNumber(record.range_points)} pts` : null,
    ].filter(Boolean);
    if (values.length) lines.push(`ORB: ${values.join(" · ")}`);
  }

  if (record.price !== null) lines.push(`Price: ${formatNumber(record.price)}`);
  if (record.side) lines.push(`State: ${record.side}`);
  if (record.bias) lines.push(`Bias: ${record.bias}`);
  if (record.setup) lines.push(`Setup: ${record.setup}`);
  if (record.target) lines.push(`Target: ${record.target}`);
  if (record.outcome) lines.push(`Outcome: ${record.outcome}`);
  if (record.note) lines.push(record.note);
  if (record.event_time) lines.push(`Time: ${record.event_time}`);

  return { content: lines.join("\n").slice(0, 1900), allowed_mentions: { parse: [] } };
}

async function postDiscord(record, env) {
  if (!env.DISCORD_WEBHOOK_URL) return;
  try {
    const response = await fetch(env.DISCORD_WEBHOOK_URL, {
      method: "POST",
      headers: { "content-type": "application/json", "user-agent": "SignalBridgeSessionWorker/1.0" },
      body: JSON.stringify(buildDiscordMessage(record)),
    });
    if (!response.ok) console.error(`Signal Bridge session Discord returned HTTP ${response.status}`);
  } catch (error) {
    console.error(`Signal Bridge session Discord delivery failed: ${error?.message || "DISCORD_ERROR"}`);
  }
}

function bearerToken(request) {
  const auth = request.headers.get("authorization") || "";
  return auth.startsWith("Bearer ") ? auth.slice(7) : "";
}

async function acceptSessionEvent(request, env, ctx, source, forceTest = false) {
  try {
    const raw = await readJson(request);
    const normalized = normalizeSessionEvent(raw, forceTest);
    const record = {
      id: crypto.randomUUID(),
      received_at: new Date().toISOString(),
      source,
      ...normalized,
    };
    await persistSessionEvent(record, env);
    if (ctx?.waitUntil) ctx.waitUntil(postDiscord(record, env));
    else await postDiscord(record, env);
    return publicJson({
      ok: true,
      accepted: true,
      session_event_id: record.id,
      session_date: record.session_date,
      stage: record.stage,
      symbol: record.symbol,
    }, 202);
  } catch (error) {
    const reason = error instanceof SyntaxError ? "invalid_json" : String(error?.message || "invalid_request");
    const status = reason === "body_too_large" ? 413 : reason === "session_storage_not_configured" ? 503 : 400;
    return publicJson({ ok: false, error: reason }, status);
  }
}

export async function handleTradingViewSessionEvent(request, env, ctx) {
  if (request.method !== "POST") return publicJson({ ok: false, error: "method_not_allowed" }, 405);
  const sourceIp = request.headers.get("cf-connecting-ip") || "";
  if (!TRADINGVIEW_IPS.has(sourceIp)) return publicJson({ ok: false, error: "source_not_allowed" }, 403);
  return acceptSessionEvent(request, env, ctx, "tradingview-session", false);
}

export async function handleTestSessionEvent(request, env, ctx) {
  if (request.method !== "POST") return publicJson({ ok: false, error: "method_not_allowed" }, 405);
  if (!env.SIGNAL_BRIDGE_TEST_TOKEN || bearerToken(request) !== env.SIGNAL_BRIDGE_TEST_TOKEN) {
    return publicJson({ ok: false, error: "unauthorized" }, 401);
  }
  return acceptSessionEvent(request, env, ctx, "authenticated-session-test", true);
}

export async function listSessionEvents(url, env) {
  if (!env.DB) return publicJson({ ok: false, error: "session_storage_not_configured" }, 503);
  const rawLimit = Number.parseInt(url.searchParams.get("limit") || "50", 10);
  const limit = Number.isFinite(rawLimit) ? Math.min(Math.max(rawLimit, 1), MAX_LIMIT) : 50;
  const symbol = safeText(url.searchParams.get("symbol"), "", 32).toUpperCase();
  const sessionDate = safeText(url.searchParams.get("session_date"), "", 10);
  const stage = safeText(url.searchParams.get("stage"), "", 32).replaceAll(" ", "_").toUpperCase();
  if (stage && !ALLOWED_STAGES.has(stage)) return publicJson({ ok: false, error: "invalid_session_stage" }, 400);

  const where = ["stage <> 'TEST'"];
  const values = [];
  const add = (column, value) => {
    values.push(value);
    where.push(`${column} = ?${values.length}`);
  };
  if (symbol) add("symbol", symbol);
  if (sessionDate) add("session_date", sessionDate);
  if (stage) add("stage", stage);
  values.push(limit);

  try {
    const result = await env.DB.prepare(
      `SELECT id, received_at, event_time, session_date, symbol, stage, side, price,
              strategy, note, timeframe, orb_high, orb_low, orb_mid, range_points,
              bias, setup, target, outcome, source
       FROM session_events
       WHERE ${where.join(" AND ")}
       ORDER BY received_at DESC
       LIMIT ?${values.length}`,
    ).bind(...values).run();
    const events = Array.isArray(result.results) ? result.results : [];
    return publicJson({ ok: true, count: events.length, events });
  } catch (error) {
    console.error(`Signal Bridge session query failed: ${error?.message || "D1_ERROR"}`);
    return publicJson({ ok: false, error: "session_query_failed" }, 500);
  }
}

export async function getLatestOrb(env, symbol = "MES") {
  if (!env.DB) return null;
  const result = await env.DB.prepare(
    `SELECT * FROM session_events
     WHERE symbol = ?1 AND stage = 'ORB_FORMED'
     ORDER BY received_at DESC LIMIT 1`,
  ).bind(safeText(symbol, "MES", 32).toUpperCase()).run();
  return Array.isArray(result.results) ? result.results[0] || null : null;
}

export async function getSessionSummaryData(env, symbol = "MES", requestedDate = null) {
  if (!env.DB) return { session_date: null, events: [], latest: null, orb: null };
  const normalizedSymbol = safeText(symbol, "MES", 32).toUpperCase();
  let sessionDate = requestedDate ? normalizeSessionDate(requestedDate) : null;
  if (!sessionDate) {
    const latestDate = await env.DB.prepare(
      `SELECT session_date FROM session_events
       WHERE symbol = ?1 AND stage <> 'TEST'
       ORDER BY session_date DESC, received_at DESC LIMIT 1`,
    ).bind(normalizedSymbol).run();
    sessionDate = Array.isArray(latestDate.results) ? latestDate.results[0]?.session_date || null : null;
  }
  if (!sessionDate) return { session_date: null, symbol: normalizedSymbol, events: [], latest: null, orb: null };

  const result = await env.DB.prepare(
    `SELECT id, received_at, event_time, session_date, symbol, stage, side, price,
            strategy, note, timeframe, orb_high, orb_low, orb_mid, range_points,
            bias, setup, target, outcome, source
     FROM session_events
     WHERE symbol = ?1 AND session_date = ?2 AND stage <> 'TEST'
     ORDER BY received_at ASC`,
  ).bind(normalizedSymbol, sessionDate).run();
  const events = Array.isArray(result.results) ? result.results : [];
  const orb = [...events].reverse().find((event) => event.stage === "ORB_FORMED") || null;
  const latest = events.length ? events[events.length - 1] : null;
  return {
    session_date: sessionDate,
    symbol: normalizedSymbol,
    event_count: events.length,
    orb,
    latest,
    events,
  };
}

export async function getSessionSummary(url, env) {
  const symbol = safeText(url.searchParams.get("symbol"), "MES", 32).toUpperCase();
  const sessionDate = safeText(url.searchParams.get("session_date"), "", 10) || null;
  try {
    const summary = await getSessionSummaryData(env, symbol, sessionDate);
    return publicJson({ ok: true, ...summary });
  } catch (error) {
    return publicJson({ ok: false, error: String(error?.message || "session_summary_failed") }, 400);
  }
}
