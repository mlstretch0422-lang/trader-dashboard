import { buildBriefText, buildNewsText, buildOrbText, buildStatusText } from "./discord_intelligence.js";

const INTERACTION_APPLICATION_COMMAND = 2;
const RESPONSE_CHANNEL_MESSAGE = 4;
const RESPONSE_DEFERRED_CHANNEL_MESSAGE = 5;
export const INTELLIGENCE_COMMANDS = new Set(["status", "orb", "brief", "news"]);

function jsonResponse(body, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "content-type": "application/json; charset=utf-8", "cache-control": "no-store" },
  });
}

function hexToBytes(hex) {
  if (typeof hex !== "string" || hex.length % 2 !== 0 || !/^[0-9a-f]+$/i.test(hex)) throw new Error("invalid_hex");
  const bytes = new Uint8Array(hex.length / 2);
  for (let i = 0; i < hex.length; i += 2) bytes[i / 2] = Number.parseInt(hex.slice(i, i + 2), 16);
  return bytes;
}

async function verifyDiscordSignature(request, publicKeyHex) {
  const signatureHex = request.headers.get("x-signature-ed25519");
  const timestamp = request.headers.get("x-signature-timestamp");
  if (!publicKeyHex || !signatureHex || !timestamp) return { ok: false, bodyText: "" };
  const bodyText = await request.text();
  try {
    const publicKey = await crypto.subtle.importKey("raw", hexToBytes(publicKeyHex), { name: "Ed25519" }, false, ["verify"]);
    const ok = await crypto.subtle.verify(
      { name: "Ed25519" },
      publicKey,
      hexToBytes(signatureHex),
      new TextEncoder().encode(`${timestamp}${bodyText}`),
    );
    return { ok, bodyText };
  } catch {
    return { ok: false, bodyText };
  }
}

function optionMap(interaction) {
  return Object.fromEntries((interaction?.data?.options || []).map((option) => [option.name, option.value]));
}

function invokingUserId(interaction) {
  return interaction?.member?.user?.id || interaction?.user?.id || null;
}

async function editOriginal(interaction, content) {
  const endpoint = `https://discord.com/api/v10/webhooks/${interaction.application_id}/${interaction.token}/messages/@original`;
  const response = await fetch(endpoint, {
    method: "PATCH",
    headers: { "content-type": "application/json", "user-agent": "SignalBridgeIntelligenceBot/1.0" },
    body: JSON.stringify({ content: String(content || "Signal Bridge completed the request.").slice(0, 1950), allowed_mentions: { parse: [] } }),
  });
  if (!response.ok) throw new Error(`discord_edit_${response.status}`);
}

async function logStart(interaction, command, env) {
  if (!env.DB) return null;
  const id = crypto.randomUUID();
  const started = Date.now();
  try {
    await env.DB.prepare(
      `INSERT INTO discord_interaction_log (
        id, received_at, completed_at, command_name, discord_user_id,
        discord_channel_id, status, error_code, duration_ms
      ) VALUES (?1, ?2, NULL, ?3, ?4, ?5, 'DEFERRED', NULL, NULL)`,
    ).bind(id, new Date().toISOString(), command, invokingUserId(interaction), interaction.channel_id || null).run();
    return { id, started };
  } catch {
    return null;
  }
}

async function logFinish(log, status, errorCode, env) {
  if (!log || !env.DB) return;
  try {
    await env.DB.prepare(
      `UPDATE discord_interaction_log
       SET completed_at = ?2, status = ?3, error_code = ?4, duration_ms = ?5
       WHERE id = ?1`,
    ).bind(log.id, new Date().toISOString(), status, errorCode || null, Date.now() - log.started).run();
  } catch {
    // Diagnostics must not break the command.
  }
}

async function runCommand(interaction, command, env) {
  const options = optionMap(interaction);
  const symbol = String(options.symbol || "MES").toUpperCase().slice(0, 32);
  if (command === "status") return buildStatusText(env);
  if (command === "orb") return buildOrbText(env, symbol);
  if (command === "brief") return buildBriefText(env, symbol);
  if (command === "news") return buildNewsText(env, options.refresh === true);
  throw new Error("unknown_intelligence_command");
}

async function completeDeferred(interaction, command, env) {
  const log = await logStart(interaction, command, env);
  try {
    const content = await runCommand(interaction, command, env);
    await editOriginal(interaction, content);
    await logFinish(log, "SUCCESS", null, env);
  } catch (error) {
    const code = String(error?.message || "intelligence_error").slice(0, 120);
    try {
      await editOriginal(interaction, "Signal Bridge could not load that intelligence view right now. The backend failure was logged for review.");
    } catch {
      // Discord may have discarded the token; the interaction log still captures the backend failure.
    }
    await logFinish(log, "FAILED", code, env);
    console.error(`Signal Bridge intelligence command failed: ${command} · ${code}`);
  }
}

export async function handleDiscordIntelligenceInteraction(request, env, ctx) {
  if (request.method !== "POST") return jsonResponse({ ok: false, error: "method_not_allowed" }, 405);
  if (!env.DISCORD_PUBLIC_KEY) return jsonResponse({ ok: false, error: "discord_interactions_not_configured" }, 503);

  const verified = await verifyDiscordSignature(request, env.DISCORD_PUBLIC_KEY);
  if (!verified.ok) return jsonResponse({ ok: false, error: "invalid_discord_signature" }, 401);

  let interaction;
  try { interaction = JSON.parse(verified.bodyText); }
  catch { return jsonResponse({ ok: false, error: "invalid_json" }, 400); }

  if (interaction.type !== INTERACTION_APPLICATION_COMMAND) {
    return jsonResponse({ type: RESPONSE_CHANNEL_MESSAGE, data: { content: "Unsupported Signal Bridge interaction." } });
  }
  if (env.DISCORD_APPLICATION_ID && interaction.application_id !== env.DISCORD_APPLICATION_ID) {
    return jsonResponse({ type: RESPONSE_CHANNEL_MESSAGE, data: { content: "This interaction belongs to a different Discord app." } });
  }
  if (env.DISCORD_GUILD_ID && interaction.guild_id !== env.DISCORD_GUILD_ID) {
    return jsonResponse({ type: RESPONSE_CHANNEL_MESSAGE, data: { content: "Signal Bridge intelligence is only enabled in the configured server." } });
  }

  const command = String(interaction?.data?.name || "").toLowerCase();
  if (!INTELLIGENCE_COMMANDS.has(command)) {
    return jsonResponse({ type: RESPONSE_CHANNEL_MESSAGE, data: { content: "Unknown Signal Bridge intelligence command." } });
  }

  const task = completeDeferred(interaction, command, env);
  if (ctx?.waitUntil) ctx.waitUntil(task);
  else task.catch((error) => console.error(error));
  return jsonResponse({ type: RESPONSE_DEFERRED_CHANNEL_MESSAGE });
}
