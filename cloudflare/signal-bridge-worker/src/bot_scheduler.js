import { buildBriefText, buildNewsText } from "./discord_intelligence.js";
import { getSessionSummaryData } from "./session_events.js";

const COLORS = {
  PREMARKET: 0x65d9ff,
  OPEN_PULSE: 0x9b7cff,
  SESSION_RECAP: 0x5ce0aa,
};

function etParts(timestampMs) {
  const parts = new Intl.DateTimeFormat("en-US", {
    timeZone: "America/New_York",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    hourCycle: "h23",
    weekday: "short",
  }).formatToParts(new Date(timestampMs));
  return Object.fromEntries(parts.map((part) => [part.type, part.value]));
}

function dispatchSpec(parts) {
  const hour = Number(parts.hour);
  const minute = Number(parts.minute);
  if (hour === 8 && minute === 45) return { kind: "PREMARKET", label: "PRE-MARKET DESK" };
  if (hour === 9 && minute === 25) return { kind: "OPEN_PULSE", label: "OPENING BELL PULSE" };
  // The Pine SESSION_CLOSE snapshot begins at 11:00 ET. Waiting ten minutes gives
  // TradingView + the Worker time to persist the close before the recap reads it.
  if (hour === 11 && minute === 10) return { kind: "SESSION_RECAP", label: "NY-AM SESSION RECAP" };
  return null;
}

function sessionDate(parts) {
  return `${parts.year}-${parts.month}-${parts.day}`;
}

async function claimDispatch(env, key, spec, date, scheduledFor) {
  if (!env.DB) return false;
  const result = await env.DB.prepare(
    `INSERT OR IGNORE INTO bot_dispatch_log (
      dispatch_key, kind, session_date, scheduled_for, attempted_at,
      completed_at, status, error_code, payload_summary
    ) VALUES (?1, ?2, ?3, ?4, ?5, NULL, 'CLAIMED', NULL, NULL)`,
  ).bind(key, spec.kind, date, scheduledFor, new Date().toISOString()).run();
  return Number(result?.meta?.changes || 0) > 0;
}

async function finishDispatch(env, key, status, errorCode = null, payloadSummary = null) {
  if (!env.DB) return;
  await env.DB.prepare(
    `UPDATE bot_dispatch_log
     SET completed_at = ?2, status = ?3, error_code = ?4, payload_summary = ?5
     WHERE dispatch_key = ?1`,
  ).bind(
    key,
    new Date().toISOString(),
    status,
    errorCode,
    String(payloadSummary || "").slice(0, 500) || null,
  ).run();
}

async function webhookPost(env, payload) {
  const endpoint = env.DISCORD_INTELLIGENCE_WEBHOOK_URL || env.DISCORD_WEBHOOK_URL;
  if (!endpoint) throw new Error("discord_intelligence_webhook_not_configured");
  const response = await fetch(endpoint, {
    method: "POST",
    headers: {
      "content-type": "application/json",
      "user-agent": "SignalBridgeDeskAssistant/2.0",
    },
    body: JSON.stringify({ ...payload, allowed_mentions: { parse: [] } }),
  });
  if (!response.ok) throw new Error(`discord_webhook_${response.status}`);
}

function cleanBuilderHeader(text) {
  return String(text || "").replace(/^.*\*\*SIGNAL BRIDGE[^\n]*\*\*\s*/i, "").trim();
}

async function buildScheduledPayload(spec, env) {
  const summary = await getSessionSummaryData(env, "MES");

  if ((spec.kind === "OPEN_PULSE" || spec.kind === "SESSION_RECAP") && !summary.session_date) {
    return { skip: true, reason: "no_session_data" };
  }

  const brief = cleanBuilderHeader(await buildBriefText(env, "MES"));
  const fields = [];
  let description = brief;

  if (spec.kind === "PREMARKET") {
    const news = cleanBuilderHeader(await buildNewsText(env, false));
    description = `${brief}\n\n${news}`.slice(0, 3950);
    fields.push({
      name: "Desk workflow",
      value: "Map the market → wait for the opening range → read the NY-open response → record the session.",
      inline: false,
    });
  }

  if (spec.kind === "OPEN_PULSE" && summary.latest) {
    fields.push({
      name: "Current lifecycle",
      value: String(summary.latest.stage || "WAIT").replaceAll("_", " ").slice(0, 1000),
      inline: true,
    });
    if (summary.orb) {
      fields.push({
        name: "ORB range",
        value: `${summary.orb.range_points ?? "—"} pts`,
        inline: true,
      });
    }
  }

  if (spec.kind === "SESSION_RECAP") {
    const latest = summary.latest || {};
    fields.push({
      name: "Closing state",
      value: `${String(latest.stage || "SESSION CLOSE").replaceAll("_", " ")}${latest.outcome ? ` · ${latest.outcome}` : ""}`.slice(0, 1000),
      inline: false,
    });
  }

  return {
    skip: false,
    payload: {
      embeds: [{
        title: `SIGNAL BRIDGE · ${spec.label}`,
        description,
        color: COLORS[spec.kind],
        fields,
        footer: { text: "Signal Bridge · hosted desk assistant · America/New_York" },
        timestamp: new Date().toISOString(),
      }],
    },
  };
}

export async function dispatchScheduledDesk(event, env) {
  const parts = etParts(event.scheduledTime || Date.now());
  const spec = dispatchSpec(parts);
  if (!spec) return { ok: true, skipped: true, reason: "not_dispatch_window" };

  const date = sessionDate(parts);
  const key = `${date}:${spec.kind}`;
  const scheduledFor = `${date}T${parts.hour}:${parts.minute}:00 America/New_York`;
  const claimed = await claimDispatch(env, key, spec, date, scheduledFor);
  if (!claimed) return { ok: true, skipped: true, reason: "already_dispatched_or_storage_unavailable", key };

  try {
    const built = await buildScheduledPayload(spec, env);
    if (built.skip) {
      await finishDispatch(env, key, "SKIPPED", built.reason, built.reason);
      return { ok: true, skipped: true, reason: built.reason, key };
    }
    await webhookPost(env, built.payload);
    await finishDispatch(env, key, "SUCCESS", null, spec.label);
    return { ok: true, dispatched: true, kind: spec.kind, key };
  } catch (error) {
    const code = String(error?.message || "scheduled_dispatch_failed").slice(0, 120);
    await finishDispatch(env, key, "FAILED", code, spec.label);
    console.error(`Signal Bridge scheduled bot dispatch failed: ${spec.kind} · ${code}`);
    return { ok: false, error: code, kind: spec.kind, key };
  }
}
