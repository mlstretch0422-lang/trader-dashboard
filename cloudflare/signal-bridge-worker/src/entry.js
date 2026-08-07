import coreWorker from "./index.js";
import { handleDiscordInteraction } from "./discord_interactions.js";
import { handleDiscordIntelligenceInteraction } from "./discord_intelligence_interactions.js";
import { handleDiscordMemberInteraction, MEMBER_COMMANDS } from "./discord_member_interactions.js";
import { handleJournalAdminRequest } from "./journal_admin.js";
import { handleMemberRequest } from "./member_app.js";
import {
  getSessionSummary,
  handleTestSessionEvent,
  handleTradingViewSessionEvent,
  listSessionEvents,
} from "./session_events.js";

const INTELLIGENCE_COMMANDS = new Set(["status", "orb", "brief"]);

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

async function extendHealth(response, env) {
  if (!response.ok) return response;
  try {
    const data = await response.clone().json();
    const [journalTable, sessionTable, memberSessions, interactionLog] = await Promise.all([
      tableReady(env, "journal_entries"),
      tableReady(env, "session_events"),
      tableReady(env, "member_sessions"),
      tableReady(env, "discord_interaction_log"),
    ]);
    return new Response(JSON.stringify({
      ...data,
      worker_release: "member-journal-reliability-v1",
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
      if (MEMBER_COMMANDS.has(command)) {
        return handleDiscordMemberInteraction(request, env, ctx);
      }
      if (INTELLIGENCE_COMMANDS.has(command)) {
        return handleDiscordIntelligenceInteraction(request, env);
      }
      return handleDiscordInteraction(request, env, ctx);
    }

    if (url.pathname === "/journal-admin" || url.pathname.startsWith("/journal-admin/")) {
      return handleJournalAdminRequest(request, env);
    }

    if (url.pathname === "/member" || url.pathname.startsWith("/member/")) {
      return handleMemberRequest(request, env);
    }

    if (url.pathname === "/tv-session") {
      return handleTradingViewSessionEvent(request, env, ctx);
    }

    if (url.pathname === "/session-test") {
      return handleTestSessionEvent(request, env, ctx);
    }

    if (request.method === "GET" && url.pathname === "/session-events") {
      return listSessionEvents(url, env);
    }

    if (request.method === "GET" && url.pathname === "/session-summary") {
      return getSessionSummary(url, env);
    }

    const response = await coreWorker.fetch(request, env, ctx);
    if (request.method === "GET" && url.pathname === "/health") {
      return extendHealth(response, env);
    }
    return response;
  },
};
