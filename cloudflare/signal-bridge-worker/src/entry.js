import coreWorker from "./index.js";
import { handleDiscordInteraction } from "./discord_interactions.js";
import { handleJournalAdminRequest } from "./journal_admin.js";
import {
  getSessionSummary,
  handleTestSessionEvent,
  handleTradingViewSessionEvent,
  listSessionEvents,
} from "./session_events.js";

async function extendHealth(response, env) {
  if (!response.ok) return response;
  try {
    const data = await response.clone().json();
    return new Response(JSON.stringify({
      ...data,
      discord_capture_configured: Boolean(
        env.DISCORD_PUBLIC_KEY &&
        env.DISCORD_APPLICATION_ID &&
        env.DISCORD_GUILD_ID &&
        env.DISCORD_JOURNAL_CHANNEL_ID
      ),
      journal_admin_configured: Boolean(env.JOURNAL_ADMIN_TOKEN || env.JOURNAL_INGEST_TOKEN),
      session_intelligence_storage: Boolean(env.DB),
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
      return handleDiscordInteraction(request, env);
    }

    if (url.pathname === "/journal-admin" || url.pathname.startsWith("/journal-admin/")) {
      return handleJournalAdminRequest(request, env);
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
