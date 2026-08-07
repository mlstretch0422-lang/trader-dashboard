import { getMarketIntelligenceSummary, refreshMarketIntelligence } from "./market_intelligence.js";
import { getLatestOrb, getSessionSummaryData } from "./session_events.js";

function safeText(value, fallback = "", maxLength = 32) {
  return String(value ?? fallback ?? "").trim().slice(0, maxLength);
}

function formatNumber(value) {
  if (value === null || value === undefined) return "—";
  const number = Number(value);
  if (!Number.isFinite(number)) return String(value);
  return Number.isInteger(number) ? String(number) : number.toFixed(2).replace(/0+$/, "").replace(/\.$/, "");
}

function stageLabel(stage) {
  return String(stage || "NO SESSION DATA").replaceAll("_", " ");
}

function formatEt(value) {
  if (!value) return "time unavailable";
  const raw = String(value);
  const parsed = new Date(raw.endsWith("Z") || /[+-]\d\d:\d\d$/.test(raw) ? raw : `${raw}Z`);
  if (!Number.isFinite(parsed.getTime())) return raw;
  return new Intl.DateTimeFormat("en-US", {
    timeZone: "America/New_York",
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
    timeZoneName: "short",
  }).format(parsed);
}

function compact(value, maxLength = 180) {
  return String(value ?? "").replace(/\s+/g, " ").trim().slice(0, maxLength);
}

async function tableReady(env, tableName) {
  if (!env.DB) return false;
  try {
    const result = await env.DB.prepare(
      `SELECT name FROM sqlite_master WHERE type = 'table' AND name = ?1 LIMIT 1`,
    ).bind(tableName).run();
    return Boolean(Array.isArray(result.results) && result.results[0]?.name === tableName);
  } catch {
    return false;
  }
}

function readiness(summary) {
  const latest = summary?.latest || {};
  const side = String(latest.side || "").toUpperCase();
  const conditions = [
    ["ORB", Boolean(summary?.orb)],
    ["Bias", Boolean(latest.bias)],
    ["Setup", Boolean(latest.setup)],
    ["Side", side === "LONG" || side === "SHORT"],
    ["Target", Boolean(latest.target)],
  ];
  const complete = conditions.filter(([, done]) => done).length;
  return {
    complete,
    total: conditions.length,
    pct: Math.round((complete / conditions.length) * 100),
    conditions,
  };
}

export async function buildStatusText(env) {
  const [signalTable, sessionTable, journalTable, memberTable, botDispatchTable] = await Promise.all([
    tableReady(env, "signal_events"),
    tableReady(env, "session_events"),
    tableReady(env, "journal_entries"),
    tableReady(env, "member_sessions"),
    tableReady(env, "bot_dispatch_log"),
  ]);
  const intel = await getMarketIntelligenceSummary(env);
  const summary = sessionTable ? await getSessionSummaryData(env, "MES") : null;
  const lines = ["**SIGNAL BRIDGE | SYSTEM STATUS**"];
  lines.push(`Worker: ONLINE`);
  lines.push(`Signal ledger: ${signalTable ? "READY" : "UNAVAILABLE"}`);
  lines.push(`Session ledger: ${sessionTable ? "READY" : "UNAVAILABLE"}`);
  lines.push(`Journal: ${journalTable ? "READY" : "UNAVAILABLE"}`);
  lines.push(`Member access: ${memberTable ? "READY" : "UNAVAILABLE"}`);
  lines.push(`Scheduled desk: ${botDispatchTable && (env.DISCORD_INTELLIGENCE_WEBHOOK_URL || env.DISCORD_WEBHOOK_URL) ? "READY" : "UNAVAILABLE"}`);
  lines.push(`Calendar: ${intel.calendar.status === "OK" && intel.calendar.fresh ? "FRESH" : "UNAVAILABLE / STALE"}`);
  lines.push(`Headlines: ${intel.headlines.status === "OK" && intel.headlines.fresh ? "FRESH" : "UNAVAILABLE / STALE"}`);
  lines.push(`Latest MES session: ${summary?.session_date || "NONE RECORDED"}${summary?.latest?.stage ? ` · ${stageLabel(summary.latest.stage)}` : ""}`);
  return lines.join("\n");
}

export async function buildOrbText(env, requestedSymbol = "MES") {
  const symbol = safeText(requestedSymbol, "MES", 32).toUpperCase();
  const orb = await getLatestOrb(env, symbol);
  if (!orb) {
    return [
      `**SIGNAL BRIDGE | ${symbol} ORB**`,
      "No ORB lifecycle record has been stored yet.",
      "When Pine lifecycle alerts are enabled, this reads the exact range recorded by the indicator.",
    ].join("\n");
  }

  const summary = await getSessionSummaryData(env, symbol, orb.session_date);
  const latest = summary.latest || {};
  const lines = [
    `**SIGNAL BRIDGE | ${symbol} ORB**`,
    `Session: ${orb.session_date}`,
    `High: ${formatNumber(orb.orb_high)}`,
    `Mid: ${formatNumber(orb.orb_mid)}`,
    `Low: ${formatNumber(orb.orb_low)}`,
    `Range: ${formatNumber(orb.range_points)} pts`,
  ];
  if (latest.price !== null && latest.price !== undefined) lines.push(`Latest price: ${formatNumber(latest.price)}`);
  if (latest.bias || orb.bias) lines.push(`Bias: ${latest.bias || orb.bias}`);
  if (latest.stage) lines.push(`Lifecycle: ${stageLabel(latest.stage)}`);
  if (latest.setup) lines.push(`Setup: ${latest.setup}`);
  if (latest.target) lines.push(`Target: ${latest.target}`);
  return lines.join("\n");
}

export async function buildBriefText(env, requestedSymbol = "MES") {
  const symbol = safeText(requestedSymbol, "MES", 32).toUpperCase();
  const summary = await getSessionSummaryData(env, symbol);
  if (!summary.session_date || !summary.events.length) {
    return [
      `**SIGNAL BRIDGE | ${symbol} SESSION BRIEF**`,
      "No recorded session lifecycle yet.",
      "The hosted brief is ready for PREMARKET → ORB → PREOPEN/OPEN → SETUP/WAIT → SESSION CLOSE events.",
    ].join("\n");
  }

  const ready = readiness(summary);
  const lines = [
    `**SIGNAL BRIDGE | ${symbol} SESSION BRIEF**`,
    `Session: ${summary.session_date}`,
    `Setup readiness: **${ready.pct}%** (${ready.complete}/${ready.total} defined conditions present)`,
  ];

  if (summary.orb) {
    lines.push(`ORB: ${formatNumber(summary.orb.orb_low)} / ${formatNumber(summary.orb.orb_mid)} / ${formatNumber(summary.orb.orb_high)} · ${formatNumber(summary.orb.range_points)} pts`);
  }

  const latest = summary.latest || {};
  if (latest.bias) lines.push(`Bias: ${latest.bias}`);
  if (latest.setup) lines.push(`Setup: ${latest.setup}`);
  if (latest.side) lines.push(`State: ${latest.side}`);
  if (latest.target) lines.push(`Target: ${latest.target}`);

  lines.push("", "**Session story**");
  const important = summary.events.filter((event) => ["PREMARKET", "PREOPEN", "OPEN_SNAPSHOT", "SETUP", "WAIT", "SESSION_CLOSE"].includes(event.stage));
  for (const event of important.slice(-6)) {
    const details = [event.side, event.setup, event.outcome].filter(Boolean).join(" · ");
    lines.push(`• ${stageLabel(event.stage)}${details ? ` — ${details}` : ""}${event.note ? ` — ${compact(event.note, 120)}` : ""}`);
  }
  lines.push("", "Readiness measures stored condition completion, not win probability.");
  return lines.join("\n").slice(0, 1900);
}

export async function buildNewsText(env, refresh = false) {
  if (refresh) await refreshMarketIntelligence(env);
  let summary = await getMarketIntelligenceSummary(env);
  if (!summary.headlines.fresh && !refresh) {
    await refreshMarketIntelligence(env);
    summary = await getMarketIntelligenceSummary(env);
  }

  const lines = ["**SIGNAL BRIDGE | MARKET INTELLIGENCE**"];
  if (summary.calendar.status !== "OK" || !summary.calendar.fresh) {
    const reason = summary.calendar.configured ? (summary.calendar.reason || "provider data is stale") : "calendar provider is not configured yet";
    lines.push(`Calendar: **UNAVAILABLE** · ${compact(reason, 100)}`);
  } else if (!summary.calendar.events.length) {
    lines.push("Calendar: no cached high-impact U.S. releases in the next 24 hours.");
  } else {
    lines.push("**High-impact U.S. calendar**");
    for (const event of summary.calendar.events.slice(0, 5)) {
      const values = [event.actual ? `Actual ${event.actual}` : null, event.forecast ? `Fcst ${event.forecast}` : null, event.previous ? `Prev ${event.previous}` : null].filter(Boolean).join(" · ");
      lines.push(`• ${formatEt(event.event_time)} · ${compact(event.event_name, 90)}${values ? ` · ${values}` : ""}`);
    }
  }

  if (summary.headlines.status === "OK" && summary.headlines.items.length) {
    lines.push("", "**Recent market headlines**");
    for (const item of summary.headlines.items.slice(0, 4)) {
      const publisher = item.publisher ? ` · ${compact(item.publisher, 45)}` : "";
      lines.push(`• ${compact(item.title, 125)}${publisher}`);
    }
  } else {
    lines.push("", "Headlines: unavailable right now.");
  }
  lines.push("", `Updated: ${formatEt(summary.generated_at)}`);
  return lines.join("\n").slice(0, 1950);
}
