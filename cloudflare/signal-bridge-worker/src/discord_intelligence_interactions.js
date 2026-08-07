import { buildBriefText, buildOrbText, buildStatusText } from "./discord_intelligence.js";

const INTERACTION_APPLICATION_COMMAND = 2;
const RESPONSE_CHANNEL_MESSAGE = 4;

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

export async function handleDiscordIntelligenceInteraction(request, env) {
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
  const options = optionMap(interaction);
  const symbol = String(options.symbol || "MES").toUpperCase().slice(0, 32);

  try {
    let content;
    if (command === "status") content = await buildStatusText(env);
    else if (command === "orb") content = await buildOrbText(env, symbol);
    else if (command === "brief") content = await buildBriefText(env, symbol);
    else content = "Unknown Signal Bridge intelligence command.";
    return jsonResponse({ type: RESPONSE_CHANNEL_MESSAGE, data: { content, allowed_mentions: { parse: [] } } });
  } catch (error) {
    console.error(`Signal Bridge intelligence command failed: ${error?.message || "INTELLIGENCE_ERROR"}`);
    return jsonResponse({
      type: RESPONSE_CHANNEL_MESSAGE,
      data: { content: "Signal Bridge could not load session intelligence right now." },
    });
  }
}
