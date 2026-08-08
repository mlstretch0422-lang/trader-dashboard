import coreWorker from "./index.js";
import { dispatchScheduledDesk } from "./bot_scheduler.js";
import { handleDiscordInteraction } from "./discord_interactions.js";
import { handleDiscordIntelligenceInteraction, INTELLIGENCE_COMMANDS } from "./discord_intelligence_interactions.js";
import { handleDiscordMemberInteraction, MEMBER_COMMANDS } from "./discord_member_interactions.js";
import { handleJournalAdminRequest } from "./journal_admin.js";
import { getMarketIntelligenceResponse, refreshMarketIntelligence } from "./market_intelligence.js";
import { handleMemberRequest } from "./member_app.js";
import {
  getSessionSummary,
  handleTestSessionEvent,
  handleTradingViewSessionEvent,
  listSessionEvents,
} from "./session_events.js";
import { handleStrategyDnaRequest } from "./strategy_dna.js";

async function discordCommandName(request) {
  if (request.method !== "POST") return "";
  try {
    const payload = JSON.parse(await request.clone().text());
    return String(payload?.data?.name || "").toLowerCase();
  } catch {
    return "";
  }
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

function bearerToken(request) {
  const auth = request.headers.get("authorization") || "";
  return auth.startsWith("Bearer ") ? auth.slice(7) : "";
}

function json(body, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "content-type": "application/json; charset=utf-8", "cache-control": "no-store" },
  });
}

async function extendHealth(response, env) {
  if (!response.ok) return response;
  try {
    const data = await response.clone().json();
    const [
      journalTable,
      sessionTable,
      memberSessions,
      interactionLog,
      intelRuns,
      calendarTable,
      headlinesTable,
      botDispatchTable,
      strategyProfiles,
      strategyVersions,
      strategyObservations,
    ] = await Promise.all([
      tableReady(env, "journal_entries"),
      tableReady(env, "session_events"),
      tableReady(env, "member_sessions"),
      tableReady(env, "discord_interaction_log"),
      tableReady(env, "market_intelligence_runs"),
      tableReady(env, "economic_calendar_events"),
      tableReady(env, "market_headlines"),
      tableReady(env, "bot_dispatch_log"),
      tableReady(env, "strategy_profiles"),
      tableReady(env, "strategy_versions"),
      tableReady(env, "strategy_observations"),
    ]);
    return new Response(JSON.stringify({
      ...data,
      worker_release: "strategy-dna-v1",
      discord_capture_configured: Boolean(
        env.DISCORD_PUBLIC_KEY &&
        env.DISCORD_APPLICATION_ID &&
        env.DISCORD_GUILD_ID &&
        env.DISCORD_JOURNAL_CHANNEL_ID
      ),
      journal_admin_configured: Boolean(env.JOURNAL_ADMIN_TOKEN || env.JOURNAL_INGEST_TOKEN),
      journal_table_ready: journalTable,
      session_table_ready: sessionTable,
      member_sessions_ready: memberSessions,
      interaction_diagnostics_ready: interactionLog,
      session_intelligence_storage: Boolean(env.DB) && sessionTable,
      market_intelligence_ready: intelRuns && calendarTable && headlinesTable,
      economic_calendar_provider_configured: Boolean(env.TRADING_ECONOMICS_API_KEY),
      scheduled_desk_ready: botDispatchTable && Boolean(env.DISCORD_INTELLIGENCE_WEBHOOK_URL || env.DISCORD_WEBHOOK_URL),
      scheduled_desk_storage_ready: botDispatchTable,
      strategy_dna_ready: strategyProfiles && strategyVersions && strategyObservations,
    }), {
      status: response.status,
      headers: response.headers,
    });
  } catch {
    return response;
  }
}

export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);

    if (url.pathname === "/discord-interactions") {
      const command = await discordCommandName(request);
      if (MEMBER_COMMANDS.has(command)) return handleDiscordMemberInteraction(request, env, ctx);
      if (INTELLIGENCE_COMMANDS.has(command)) return handleDiscordIntelligenceInteraction(request, env, ctx);
      return handleDiscordInteraction(request, env, ctx);
    }

    if (url.pathname === "/journal-admin" || url.pathname.startsWith("/journal-admin/")) {
      return handleJournalAdminRequest(request, env);
    }

    if (url.pathname === "/member" || url.pathname.startsWith("/member/")) {
      return handleMemberRequest(request, env);
    }

    if (url.pathname === "/strategy-dna" || url.pathname.startsWith("/strategy-dna/")) {
      return handleStrategyDnaRequest(request, env);
    }

    if (url.pathname === "/tv-session") return handleTradingViewSessionEvent(request, env, ctx);
    if (url.pathname === "/session-test") return handleTestSessionEvent(request, env, ctx);
    if (request.method === "GET" && url.pathname === "/session-events") return listSessionEvents(url, env);
    if (request.method === "GET" && url.pathname === "/session-summary") return getSessionSummary(url, env);
    if (request.method === "GET" && url.pathname === "/market-intelligence") return getMarketIntelligenceResponse(env);

    if (request.method === "POST" && url.pathname === "/market-intelligence/refresh") {
      if (!env.SIGNAL_BRIDGE_TEST_TOKEN || bearerToken(request) !== env.SIGNAL_BRIDGE_TEST_TOKEN) {
        return json({ ok: false, error: "unauthorized" }, 401);
      }
      const result = await refreshMarketIntelligence(env);
      return json({ ok: true, results: result });
    }

    const response = await coreWorker.fetch(request, env, ctx);
    if (request.method === "GET" && url.pathname === "/health") return extendHealth(response, env);
    return response;
  },

  async scheduled(event, env, ctx) {
    const cron = String(event.cron || "");
    if (cron === "*/15 * * * *") {
      ctx.waitUntil(refreshMarketIntelligence(env));
      return;
    }
    if (cron === "*/5 12-17 * * 1-5") {
      ctx.waitUntil(dispatchScheduledDesk(event, env));
      return;
    }
    ctx.waitUntil(Promise.all([
      refreshMarketIntelligence(env),
      dispatchScheduledDesk(event, env),
    ]));
  },
};
