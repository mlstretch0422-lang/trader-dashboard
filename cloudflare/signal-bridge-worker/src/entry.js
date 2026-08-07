import coreWorker from "./index.js";
import { handleDiscordInteraction } from "./discord_interactions.js";

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

    const response = await coreWorker.fetch(request, env, ctx);
    if (request.method === "GET" && url.pathname === "/health") {
      return extendHealth(response, env);
    }
    return response;
  },
};
