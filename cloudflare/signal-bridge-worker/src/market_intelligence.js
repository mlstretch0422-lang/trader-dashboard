const CALENDAR_PROVIDER = "trading-economics";
const HEADLINE_PROVIDER = "yahoo-finance";
const MAX_HEADLINES = 8;
const RUN_FRESH_MINUTES = 45;

function safeText(value, maxLength = 500) {
  return String(value ?? "").trim().slice(0, maxLength);
}

function isoNow() {
  return new Date().toISOString();
}

function etDate(date = new Date()) {
  const parts = new Intl.DateTimeFormat("en-US", {
    timeZone: "America/New_York",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  }).formatToParts(date);
  const map = Object.fromEntries(parts.map((part) => [part.type, part.value]));
  return `${map.year}-${map.month}-${map.day}`;
}

function addDaysEt(days) {
  return etDate(new Date(Date.now() + days * 86_400_000));
}

async function sha256(value) {
  const digest = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(String(value)));
  return [...new Uint8Array(digest)].map((byte) => byte.toString(16).padStart(2, "0")).join("");
}

async function beginRun(env, provider, dataType) {
  const run = { id: crypto.randomUUID(), started_at: isoNow(), provider, data_type: dataType };
  if (env.DB) {
    await env.DB.prepare(
      `INSERT INTO market_intelligence_runs (
        id, started_at, completed_at, provider, data_type, status,
        item_count, error_code, source_timestamp
      ) VALUES (?1, ?2, NULL, ?3, ?4, 'UNAVAILABLE', 0, NULL, NULL)`,
    ).bind(run.id, run.started_at, provider, dataType).run();
  }
  return run;
}

async function finishRun(env, run, status, itemCount = 0, errorCode = null, sourceTimestamp = null) {
  if (!env.DB) return;
  await env.DB.prepare(
    `UPDATE market_intelligence_runs
     SET completed_at = ?2, status = ?3, item_count = ?4, error_code = ?5, source_timestamp = ?6
     WHERE id = ?1`,
  ).bind(run.id, isoNow(), status, itemCount, errorCode, sourceTimestamp).run();
}

function normalizeCalendarItem(item) {
  return {
    provider_event_id: safeText(item.CalendarId, 96) || null,
    event_time: safeText(item.Date, 96),
    country: safeText(item.Country, 80) || null,
    category: safeText(item.Category, 120) || null,
    event_name: safeText(item.Event || item.Category, 180),
    importance: Number.isFinite(Number(item.Importance)) ? Number(item.Importance) : null,
    actual: safeText(item.Actual, 80) || null,
    previous: safeText(item.Previous, 80) || null,
    forecast: safeText(item.Forecast, 80) || null,
    provider_forecast: safeText(item.TEForecast, 80) || null,
    source_name: safeText(item.Source, 180) || null,
    source_url: safeText(item.SourceURL, 500) || null,
    provider_url: safeText(item.URL, 500) || null,
    last_update: safeText(item.LastUpdate, 96) || null,
    payload_json: JSON.stringify(item),
  };
}

async function persistCalendarItems(env, items, fetchedAt) {
  if (!env.DB) throw new Error("market_intelligence_storage_not_configured");
  const statements = [];
  for (const raw of items) {
    const item = normalizeCalendarItem(raw);
    if (!item.event_time || !item.event_name) continue;
    const providerEventId = item.provider_event_id || await sha256(`${item.event_time}|${item.country}|${item.event_name}`);
    const id = await sha256(`${CALENDAR_PROVIDER}|${providerEventId}`);
    statements.push(env.DB.prepare(
      `INSERT INTO economic_calendar_events (
        id, provider, provider_event_id, event_time, country, category, event_name,
        importance, actual, previous, forecast, provider_forecast, source_name,
        source_url, provider_url, last_update, fetched_at, payload_json
      ) VALUES (
        ?1, ?2, ?3, ?4, ?5, ?6, ?7, ?8, ?9,
        ?10, ?11, ?12, ?13, ?14, ?15, ?16, ?17, ?18
      )
      ON CONFLICT(provider, provider_event_id) DO UPDATE SET
        event_time = excluded.event_time,
        country = excluded.country,
        category = excluded.category,
        event_name = excluded.event_name,
        importance = excluded.importance,
        actual = excluded.actual,
        previous = excluded.previous,
        forecast = excluded.forecast,
        provider_forecast = excluded.provider_forecast,
        source_name = excluded.source_name,
        source_url = excluded.source_url,
        provider_url = excluded.provider_url,
        last_update = excluded.last_update,
        fetched_at = excluded.fetched_at,
        payload_json = excluded.payload_json`,
    ).bind(
      id,
      CALENDAR_PROVIDER,
      providerEventId,
      item.event_time,
      item.country,
      item.category,
      item.event_name,
      item.importance,
      item.actual,
      item.previous,
      item.forecast,
      item.provider_forecast,
      item.source_name,
      item.source_url,
      item.provider_url,
      item.last_update,
      fetchedAt,
      item.payload_json,
    ));
  }
  for (let i = 0; i < statements.length; i += 50) await env.DB.batch(statements.slice(i, i + 50));
  return statements.length;
}

export async function refreshEconomicCalendar(env) {
  const run = await beginRun(env, CALENDAR_PROVIDER, "ECONOMIC_CALENDAR");
  if (!env.TRADING_ECONOMICS_API_KEY) {
    await finishRun(env, run, "UNAVAILABLE", 0, "provider_not_configured");
    return { ok: false, status: "UNAVAILABLE", provider: CALENDAR_PROVIDER, error: "provider_not_configured", count: 0 };
  }

  const startDate = etDate();
  const endDate = addDaysEt(1);
  const endpoint = `https://api.tradingeconomics.com/calendar/country/united%20states/${startDate}/${endDate}?importance=3&f=json`;
  try {
    const response = await fetch(endpoint, {
      headers: {
        Authorization: env.TRADING_ECONOMICS_API_KEY,
        "user-agent": "SignalBridgeWorker/market-intelligence-v1",
      },
    });
    if (!response.ok) throw new Error(`provider_http_${response.status}`);
    const payload = await response.json();
    if (!Array.isArray(payload)) throw new Error("provider_payload_invalid");
    const fetchedAt = isoNow();
    const count = await persistCalendarItems(env, payload, fetchedAt);
    const sourceTimestamp = payload.map((item) => item.LastUpdate).filter(Boolean).sort().at(-1) || null;
    await finishRun(env, run, "OK", count, null, sourceTimestamp);
    return { ok: true, status: "OK", provider: CALENDAR_PROVIDER, count };
  } catch (error) {
    const code = safeText(error?.message || "calendar_refresh_failed", 120);
    await finishRun(env, run, "ERROR", 0, code);
    return { ok: false, status: "ERROR", provider: CALENDAR_PROVIDER, error: code, count: 0 };
  }
}

function yahooItems(payload) {
  return Array.isArray(payload?.news) ? payload.news.slice(0, MAX_HEADLINES) : [];
}

async function persistHeadlines(env, items, fetchedAt, symbol) {
  if (!env.DB) throw new Error("market_intelligence_storage_not_configured");
  const statements = [];
  for (const item of items) {
    const title = safeText(item.title, 300);
    if (!title) continue;
    const url = safeText(item.link || item.url, 800) || null;
    const providerItemId = safeText(item.uuid || item.id, 160) || await sha256(`${title}|${url || ""}`);
    const id = await sha256(`${HEADLINE_PROVIDER}|${providerItemId}`);
    const publishedUnix = Number(item.providerPublishTime || item.published_at || item.pubDate || 0);
    const publishedAt = Number.isFinite(publishedUnix) && publishedUnix > 0
      ? new Date(publishedUnix * 1000).toISOString()
      : null;
    statements.push(env.DB.prepare(
      `INSERT INTO market_headlines (
        id, provider, provider_item_id, published_at, title, publisher, url,
        symbol, fetched_at, payload_json
      ) VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7, ?8, ?9, ?10)
      ON CONFLICT(provider, provider_item_id) DO UPDATE SET
        published_at = excluded.published_at,
        title = excluded.title,
        publisher = excluded.publisher,
        url = excluded.url,
        symbol = excluded.symbol,
        fetched_at = excluded.fetched_at,
        payload_json = excluded.payload_json`,
    ).bind(
      id,
      HEADLINE_PROVIDER,
      providerItemId,
      publishedAt,
      title,
      safeText(item.publisher, 180) || null,
      url,
      symbol,
      fetchedAt,
      JSON.stringify(item),
    ));
  }
  for (let i = 0; i < statements.length; i += 50) await env.DB.batch(statements.slice(i, i + 50));
  return statements.length;
}

export async function refreshHeadlines(env, symbol = "SPY") {
  const run = await beginRun(env, HEADLINE_PROVIDER, "HEADLINES");
  const normalizedSymbol = safeText(symbol || "SPY", 16).toUpperCase();
  const endpoint = `https://query1.finance.yahoo.com/v1/finance/search?q=${encodeURIComponent(normalizedSymbol)}&quotesCount=0&newsCount=${MAX_HEADLINES}`;
  try {
    const response = await fetch(endpoint, { headers: { "user-agent": "SignalBridgeWorker/market-intelligence-v1" } });
    if (!response.ok) throw new Error(`provider_http_${response.status}`);
    const payload = await response.json();
    const items = yahooItems(payload);
    const count = await persistHeadlines(env, items, isoNow(), normalizedSymbol);
    await finishRun(env, run, "OK", count, null, null);
    return { ok: true, status: "OK", provider: HEADLINE_PROVIDER, count };
  } catch (error) {
    const code = safeText(error?.message || "headline_refresh_failed", 120);
    await finishRun(env, run, "ERROR", 0, code);
    return { ok: false, status: "ERROR", provider: HEADLINE_PROVIDER, error: code, count: 0 };
  }
}

export async function refreshMarketIntelligence(env) {
  const results = await Promise.allSettled([
    refreshEconomicCalendar(env),
    refreshHeadlines(env, "SPY"),
  ]);
  return results.map((result) => result.status === "fulfilled"
    ? result.value
    : { ok: false, status: "ERROR", error: safeText(result.reason?.message || result.reason, 120) });
}

async function latestRun(env, dataType) {
  if (!env.DB) return null;
  const result = await env.DB.prepare(
    `SELECT * FROM market_intelligence_runs
     WHERE data_type = ?1
     ORDER BY started_at DESC LIMIT 1`,
  ).bind(dataType).run();
  return Array.isArray(result.results) ? result.results[0] || null : null;
}

function runFresh(run) {
  if (!run?.completed_at) return false;
  const time = Date.parse(run.completed_at);
  return Number.isFinite(time) && Date.now() - time <= RUN_FRESH_MINUTES * 60_000;
}

export async function getMarketIntelligenceSummary(env) {
  if (!env.DB) return {
    calendar: { status: "UNAVAILABLE", reason: "storage_not_configured", fresh: false, events: [] },
    headlines: { status: "UNAVAILABLE", reason: "storage_not_configured", fresh: false, items: [] },
  };

  const [calendarRun, headlineRun] = await Promise.all([
    latestRun(env, "ECONOMIC_CALENDAR"),
    latestRun(env, "HEADLINES"),
  ]);

  const now = new Date();
  const windowStart = new Date(now.getTime() - 60 * 60_000).toISOString().slice(0, 19);
  const windowEnd = new Date(now.getTime() + 24 * 60 * 60_000).toISOString().slice(0, 19);
  const calendarResult = await env.DB.prepare(
    `SELECT id, provider, provider_event_id, event_time, country, category, event_name,
            importance, actual, previous, forecast, provider_forecast, source_name,
            source_url, provider_url, last_update, fetched_at
     FROM economic_calendar_events
     WHERE event_time >= ?1 AND event_time <= ?2
     ORDER BY event_time ASC, importance DESC
     LIMIT 20`,
  ).bind(windowStart, windowEnd).run();

  const headlineResult = await env.DB.prepare(
    `SELECT id, provider, published_at, title, publisher, url, symbol, fetched_at
     FROM market_headlines
     ORDER BY COALESCE(published_at, fetched_at) DESC
     LIMIT 6`,
  ).run();

  return {
    generated_at: isoNow(),
    calendar: {
      provider: CALENDAR_PROVIDER,
      configured: Boolean(env.TRADING_ECONOMICS_API_KEY),
      status: calendarRun?.status || "UNAVAILABLE",
      reason: calendarRun?.error_code || null,
      fresh: runFresh(calendarRun),
      last_refresh: calendarRun?.completed_at || null,
      events: Array.isArray(calendarResult.results) ? calendarResult.results : [],
    },
    headlines: {
      provider: HEADLINE_PROVIDER,
      status: headlineRun?.status || "UNAVAILABLE",
      reason: headlineRun?.error_code || null,
      fresh: runFresh(headlineRun),
      last_refresh: headlineRun?.completed_at || null,
      items: Array.isArray(headlineResult.results) ? headlineResult.results : [],
    },
  };
}

export async function getMarketIntelligenceResponse(env) {
  const summary = await getMarketIntelligenceSummary(env);
  return new Response(JSON.stringify({ ok: true, ...summary }), {
    status: 200,
    headers: {
      "content-type": "application/json; charset=utf-8",
      "cache-control": "no-store",
      "access-control-allow-origin": "*",
    },
  });
}
