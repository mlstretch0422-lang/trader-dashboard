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
  const parsed = new Date(value.endsWith?.("Z") || /[+-]\d\d:\d\d$/.test(value) ? value : `${value}Z`);
  if (!Number.isFinite(parsed.getTime())) return String(value);
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

export async function buildStatusText(env) {
  const checks = [
    ["Worker", "ONLINE"],
    ["Signal ledger", env.DB ? "CONNECTED" : "OFFLINE"],
    ["Session ledger", env.DB ? "CONNECTED" : "OFFLINE"],
    ["Discord journal", env.DISCORD_PUBLIC_KEY && env.DISCORD_JOURNAL_CHANNEL_ID ? "CONNECTED" : "NOT CONFIGURED"],
    ["Member journal", env.DB ? "AVAILABLE AFTER LOGIN" : "OFFLINE"],
    ["Economic calendar", env.TRADING_ECONOMICS_API_KEY ? "PROVIDER CONFIGURED" : "PROVIDER NOT CONFIGURED"],
  ];
  const lines = ["🟢 **SIGNAL BRIDGE | STATUS**"];
  for (const [name, value] of checks) lines.push(`${name}: ${value}`);
  lines.push("Signal, session, journal, and intelligence services are hosted independently of the local Mac.");
  return lines.join("\n");
}

export async function buildOrbText(env, requestedSymbol = "MES") {
  const symbol = safeText(requestedSymbol, "MES", 32).toUpperCase();
  const orb = await getLatestOrb(env, symbol);
  if (!orb) {
    return [
      `📦 **SIGNAL BRIDGE | ${symbol} ORB**`,
      "No ORB lifecycle record has been stored yet.",
      "When the Pine lifecycle alerts are enabled, this command will read the exact opening range that the indicator recorded.",
    ].join("\n");
  }

  const lines = [
    `📦 **SIGNAL BRIDGE | ${symbol} ORB**`,
    `Session: ${orb.session_date}`,
    `High: ${formatNumber(orb.orb_high)}`,
    `Mid: ${formatNumber(orb.orb_mid)}`,
    `Low: ${formatNumber(orb.orb_low)}`,
    `Range: ${formatNumber(orb.range_points)} pts`,
  ];
  if (orb.bias) lines.push(`Bias: ${orb.bias}`);
  if (orb.note) lines.push(`Note: ${orb.note}`);
  return lines.join("\n");
}

export async function buildBriefText(env, requestedSymbol = "MES") {
  const symbol = safeText(requestedSymbol, "MES", 32).toUpperCase();
  const summary = await getSessionSummaryData(env, symbol);
  if (!summary.session_date || !summary.events.length) {
    return [
      `🧭 **SIGNAL BRIDGE | ${symbol} SESSION BRIEF**`,
      "No recorded session lifecycle yet.",
      "Once connected, this brief builds from PREMARKET → ORB → PREOPEN/OPEN → SETUP/WAIT → SESSION CLOSE.",
    ].join("\n");
  }

  const lines = [
    `🧭 **SIGNAL BRIDGE | ${symbol} SESSION BRIEF**`,
    `Session: ${summary.session_date}`,
  ];

  if (summary.orb) {
    lines.push(`ORB: ${formatNumber(summary.orb.orb_low)} / ${formatNumber(summary.orb.orb_mid)} / ${formatNumber(summary.orb.orb_high)} · ${formatNumber(summary.orb.range_points)} pts`);
  }

  const important = summary.events.filter((event) => ["PREMARKET", "PREOPEN", "OPEN_SNAPSHOT", "SETUP", "WAIT", "SESSION_CLOSE"].includes(event.stage));
  for (const event of important.slice(-6)) {
    const details = [event.side, event.setup, event.outcome, event.bias].filter(Boolean).join(" · ");
    lines.push(`${stageLabel(event.stage)}${details ? ` — ${details}` : ""}${event.note ? ` — ${event.note}` : ""}`);
  }

  if (summary.latest) lines.push(`Latest: ${stageLabel(summary.latest.stage)}`);
  return lines.join("\n").slice(0, 1900);
}

export async function buildNewsText(env, refresh = false) {
  if (refresh) await refreshMarketIntelligence(env);
  let summary = await getMarketIntelligenceSummary(env);

  // A command can repair an empty/stale headline cache without waiting for the next cron.
  if (!summary.headlines.fresh && !refresh) {
    await refreshMarketIntelligence(env);
    summary = await getMarketIntelligenceSummary(env);
  }

  const lines = ["📰 **SIGNAL BRIDGE | MARKET INTELLIGENCE**"];

  if (summary.calendar.status !== "OK" || !summary.calendar.fresh) {
    const reason = summary.calendar.configured
      ? (summary.calendar.reason || "provider data is stale")
      : "calendar provider is not configured yet";
    lines.push(`Calendar: **UNAVAILABLE** · ${compact(reason, 100)}`);
  } else if (!summary.calendar.events.length) {
    lines.push("Calendar: no cached high-impact U.S. releases in the next 24 hours.");
  } else {
    lines.push("**High-impact U.S. calendar**");
    for (const event of summary.calendar.events.slice(0, 5)) {
      const values = [
        event.actual ? `Actual ${event.actual}` : null,
        event.forecast ? `Fcst ${event.forecast}` : null,
        event.previous ? `Prev ${event.previous}` : null,
      ].filter(Boolean).join(" · ");
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
