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

export async function buildStatusText(env) {
  const checks = [
    ["Worker", "ONLINE"],
    ["Signal ledger", env.DB ? "CONNECTED" : "OFFLINE"],
    ["Session ledger", env.DB ? "CONNECTED" : "OFFLINE"],
    ["Discord journal", env.DISCORD_PUBLIC_KEY && env.DISCORD_JOURNAL_CHANNEL_ID ? "CONNECTED" : "NOT CONFIGURED"],
    ["Journal admin", env.JOURNAL_ADMIN_TOKEN || env.JOURNAL_INGEST_TOKEN ? "READY" : "NOT CONFIGURED"],
  ];
  const lines = ["🟢 **SIGNAL BRIDGE | STATUS**"];
  for (const [name, value] of checks) lines.push(`${name}: ${value}`);
  lines.push("Hosted signal, session-intelligence, and journal services are independent of the local Mac.");
  return lines.join("\n");
}

export async function buildOrbText(env, requestedSymbol = "MES") {
  const symbol = safeText(requestedSymbol, "MES", 32).toUpperCase();
  const orb = await getLatestOrb(env, symbol);
  if (!orb) {
    return [
      `📦 **SIGNAL BRIDGE | ${symbol} ORB**`,
      "No ORB_FORMED session event has been stored yet.",
      "Once the Pine lifecycle alert is enabled, this command will read the last recorded ORB directly from the session ledger.",
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
      "The brief will build itself from PREMARKET → ORB_FORMED → PREOPEN/OPEN → SETUP/WAIT → SESSION_CLOSE events.",
    ].join("\n");
  }

  const lines = [
    `🧭 **SIGNAL BRIDGE | ${symbol} SESSION BRIEF**`,
    `Session: ${summary.session_date}`,
    `Events recorded: ${summary.events.length}`,
  ];

  if (summary.orb) {
    lines.push(`ORB: ${formatNumber(summary.orb.orb_low)} / ${formatNumber(summary.orb.orb_mid)} / ${formatNumber(summary.orb.orb_high)} · ${formatNumber(summary.orb.range_points)} pts`);
  }

  const important = summary.events.filter((event) => ["PREMARKET", "PREOPEN", "OPEN_SNAPSHOT", "SETUP", "WAIT", "SESSION_CLOSE"].includes(event.stage));
  for (const event of important.slice(-6)) {
    const details = [
      event.side,
      event.setup,
      event.outcome,
      event.bias,
    ].filter(Boolean).join(" · ");
    lines.push(`${stageLabel(event.stage)}${details ? ` — ${details}` : ""}${event.note ? ` — ${event.note}` : ""}`);
  }

  if (summary.latest) lines.push(`Latest state: ${stageLabel(summary.latest.stage)}`);
  return lines.join("\n").slice(0, 1900);
}
