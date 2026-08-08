import { createMemberLoginLink } from "./member_app.js";

const INTERACTION_APPLICATION_COMMAND = 2;
const RESPONSE_DEFERRED_CHANNEL_MESSAGE = 5;
const MESSAGE_EPHEMERAL = 1 << 6;
const PERMISSION_ADMINISTRATOR = 1n << 3n;
const PERMISSION_MANAGE_GUILD = 1n << 5n;
const JOURNAL_URL = "https://mlstretch0422-lang.github.io/trader-dashboard/journal.html";

export const MEMBER_COMMANDS = new Set([
  "start",
  "journal-inbox",
  "journal-update",
  "journal-publish",
  "journal-private",
  "journal-login",
  "member-login",
]);

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

function invokingUserId(interaction) {
  return interaction?.member?.user?.id || interaction?.user?.id || null;
}

function canManage(interaction) {
  try {
    const permissions = BigInt(interaction?.member?.permissions || "0");
    return Boolean(permissions & PERMISSION_ADMINISTRATOR) || Boolean(permissions & PERMISSION_MANAGE_GUILD);
  } catch {
    return false;
  }
}

function optionMap(interaction) {
  return Object.fromEntries((interaction?.data?.options || []).map((option) => [option.name, option.value]));
}

function hasOption(options, key) {
  return Object.prototype.hasOwnProperty.call(options, key);
}

function compact(value, maxLength = 160) {
  return String(value ?? "").trim().replace(/\s+/g, " ").slice(0, maxLength);
}

function deferEphemeral() {
  return jsonResponse({ type: RESPONSE_DEFERRED_CHANNEL_MESSAGE, data: { flags: MESSAGE_EPHEMERAL } });
}

async function editOriginal(interaction, content) {
  const endpoint = `https://discord.com/api/v10/webhooks/${interaction.application_id}/${interaction.token}/messages/@original`;
  const response = await fetch(endpoint, {
    method: "PATCH",
    headers: { "content-type": "application/json", "user-agent": "SignalBridgeMemberBot/2.2" },
    body: JSON.stringify({ content: String(content || "Signal Bridge completed the request.").slice(0, 1950), allowed_mentions: { parse: [] } }),
  });
  if (!response.ok) throw new Error(`discord_edit_${response.status}`);
}

async function logStart(interaction, command, env) {
  if (!env.DB) return null;
  const id = crypto.randomUUID();
  const now = new Date().toISOString();
  try {
    await env.DB.prepare(
      `INSERT INTO discord_interaction_log (
        id, received_at, completed_at, command_name, discord_user_id,
        discord_channel_id, status, error_code, duration_ms
      ) VALUES (?1, ?2, NULL, ?3, ?4, ?5, 'DEFERRED', NULL, NULL)`,
    ).bind(id, now, command, invokingUserId(interaction), interaction.channel_id || null).run();
    return { id, started: Date.now() };
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
    // Diagnostics must never break the user command.
  }
}

function resolveEntitlement(interaction, env) {
  if (canManage(interaction)) return { tier: "ADMIN", source: "DISCORD_MANAGER" };
  const premiumRoleId = compact(env.DISCORD_PREMIUM_ROLE_ID, 64);
  if (!premiumRoleId) {
    // Friends/family beta mode: every member of the configured guild can enter.
    // Set DISCORD_PREMIUM_ROLE_ID before a paid launch to switch to role gating.
    return { tier: "BETA", source: "DISCORD_BETA" };
  }
  const roles = Array.isArray(interaction?.member?.roles) ? interaction.member.roles.map(String) : [];
  if (roles.includes(premiumRoleId)) return { tier: "PREMIUM", source: "DISCORD_PREMIUM_ROLE" };
  throw new Error("premium_role_required");
}

async function syncEntitlement(interaction, env) {
  if (!env.DB) throw new Error("member_storage_not_configured");
  const userId = invokingUserId(interaction);
  if (!userId) throw new Error("discord_user_missing");
  const access = resolveEntitlement(interaction, env);
  const now = new Date().toISOString();
  await env.DB.prepare(
    `INSERT INTO member_entitlements (
       discord_user_id, discord_guild_id, tier, status, source,
       granted_at, updated_at, expires_at, metadata_json
     ) VALUES (?1, ?2, ?3, 'ACTIVE', ?4, ?5, ?5, NULL, ?6)
     ON CONFLICT(discord_user_id) DO UPDATE SET
       discord_guild_id = excluded.discord_guild_id,
       tier = excluded.tier,
       status = 'ACTIVE',
       source = excluded.source,
       updated_at = excluded.updated_at,
       expires_at = NULL,
       metadata_json = excluded.metadata_json`,
  ).bind(
    userId,
    interaction.guild_id || null,
    access.tier,
    access.source,
    now,
    JSON.stringify({ premium_role_configured: Boolean(env.DISCORD_PREMIUM_ROLE_ID) }),
  ).run();
  return access;
}

function buildStartGuide() {
  return [
    "👋 **SIGNAL BRIDGE | START HERE**",
    "Signal Bridge helps you turn a trade idea into a record you can actually review instead of losing it in screenshots, chat, or memory.",
    "",
    "**Before the trade**",
    "Use `/journal` and set Result to **Open**. Save what you see, the setup, where the idea came from, and a chart if you have one.",
    "",
    "**After the trade**",
    "Use `/journal-update id:<ID>` to add the final result, P&L, R, and lesson. Your original pre-trade note stays preserved.",
    "",
    "**Already finished?**",
    "Use `/journal` once with the chart + final result + P&L/R.",
    "",
    "**Need the desk?** `/brief` = session story · `/orb` = opening range · `/news` = calendar/headlines.",
    "**Need your records?** `/journal-inbox` = recent trades · `/member-login` = private website workspace + Strategy Lab.",
    "",
    "Saw a setup on TikTok/Discord? Log the source in the note. One winner does **not** validate the creator or setup — the value comes from building a repeatable sample.",
  ].join("\n");
}

async function listJournalForUser(interaction, env) {
  const userId = invokingUserId(interaction);
  if (!env.DB) throw new Error("journal_storage_not_configured");
  if (!userId) throw new Error("discord_user_missing");
  const options = optionMap(interaction);
  const requestedLimit = Number(options.limit || 5);
  const limit = Number.isFinite(requestedLimit) ? Math.min(Math.max(Math.trunc(requestedLimit), 1), 5) : 5;
  const status = compact(options.status || "ALL", 16).toUpperCase();
  const visibility = ["PRIVATE", "PUBLISHED", "ALL"].includes(status) ? status : "ALL";

  const values = [userId];
  let where = "discord_author_id = ?1";
  if (visibility !== "ALL") {
    values.push(visibility);
    where += ` AND visibility = ?${values.length}`;
  }
  values.push(limit);

  const result = await env.DB.prepare(
    `SELECT id, created_at, journal_time, symbol, side, setup, title, raw_text,
            summary, result, pnl, rr, image_url, visibility, review_status
     FROM journal_entries
     WHERE ${where}
     ORDER BY COALESCE(journal_time, created_at) DESC
     LIMIT ?${values.length}`,
  ).bind(...values).run();
  const entries = Array.isArray(result.results) ? result.results : [];
  if (!entries.length) {
    return [
      "📚 **SIGNAL BRIDGE | JOURNAL INBOX**",
      `No ${visibility.toLowerCase()} records are linked to your Discord account yet.`,
      "Start with `/journal` or run `/start` for the 30-second workflow.",
    ].join("\n");
  }

  const lines = ["📚 **SIGNAL BRIDGE | JOURNAL INBOX**", `${visibility} · ${entries.length} recent record${entries.length === 1 ? "" : "s"}`];
  for (const entry of entries) {
    const identity = [entry.symbol, entry.side, entry.result].filter(Boolean).join(" | ") || "Unclassified";
    lines.push("");
    lines.push(`**${entry.id.slice(0, 8)}** · ${entry.visibility} · ${identity}`);
    if (entry.setup) lines.push(`Setup: ${compact(entry.setup, 60)}`);
    if (entry.pnl !== null && entry.pnl !== undefined) lines.push(`P&L: ${entry.pnl}`);
    if (entry.rr !== null && entry.rr !== undefined) lines.push(`R: ${entry.rr}`);
    lines.push(compact(entry.summary || entry.raw_text, 115));
    if (entry.image_url) lines.push(`Chart: ${entry.image_url}`);
  }
  lines.push("", "Use `/journal-update id:<ID>` to close out an OPEN trade. Use `/member-login` for the private workspace.");
  return lines.join("\n");
}

async function resolveJournalForUser(idValue, userId, env) {
  const id = compact(idValue, 64);
  if (id.length < 6) throw new Error("journal_id_too_short");
  const result = await env.DB.prepare(
    `SELECT * FROM journal_entries
     WHERE discord_author_id = ?1 AND id LIKE ?2
     ORDER BY created_at DESC LIMIT 2`,
  ).bind(userId, `${id}%`).run();
  const rows = Array.isArray(result.results) ? result.results : [];
  if (!rows.length) throw new Error("journal_not_found");
  if (rows.length > 1) throw new Error("journal_id_ambiguous");
  return rows[0];
}

async function updateOwnJournal(interaction, env) {
  if (!env.DB) throw new Error("journal_storage_not_configured");
  const userId = invokingUserId(interaction);
  if (!userId) throw new Error("discord_user_missing");
  const options = optionMap(interaction);
  const entry = await resolveJournalForUser(options.id, userId, env);

  const hasResult = hasOption(options, "result");
  const hasPnl = hasOption(options, "pnl");
  const hasRr = hasOption(options, "rr");
  const hasReview = hasOption(options, "review");
  if (!hasResult && !hasPnl && !hasRr && !hasReview) throw new Error("journal_update_empty");

  const result = hasResult ? compact(options.result, 16).toUpperCase() : entry.result;
  const pnl = hasPnl ? Number(options.pnl) : entry.pnl;
  const rr = hasRr ? Number(options.rr) : entry.rr;
  const review = hasReview ? compact(options.review, 1000) : entry.summary;
  if (hasPnl && !Number.isFinite(pnl)) throw new Error("journal_update_invalid_number");
  if (hasRr && !Number.isFinite(rr)) throw new Error("journal_update_invalid_number");

  await env.DB.prepare(
    `UPDATE journal_entries
     SET result = ?2, pnl = ?3, rr = ?4, summary = ?5
     WHERE id = ?1 AND discord_author_id = ?6`,
  ).bind(entry.id, result, pnl, rr, review || null, userId).run();

  const lines = ["✅ **SIGNAL BRIDGE | JOURNAL UPDATED**", `ID: ${entry.id.slice(0, 8)}`];
  if (result) lines.push(`Result: ${result}`);
  if (pnl !== null && pnl !== undefined) lines.push(`P&L: ${pnl}`);
  if (rr !== null && rr !== undefined) lines.push(`R: ${rr}`);
  if (hasReview && review) lines.push(`Review: ${review}`);
  lines.push("Original pre-trade note preserved. Run `/journal-inbox` to see the updated record.");
  return lines.join("\n");
}

async function setJournalVisibility(interaction, visibility, env) {
  if (!canManage(interaction)) throw new Error("manager_permission_required");
  const userId = invokingUserId(interaction);
  const id = optionMap(interaction).id;
  const entry = await resolveJournalForUser(id, userId, env);
  const reviewStatus = visibility === "PUBLISHED" ? "REVIEWED" : entry.review_status;
  await env.DB.prepare(
    `UPDATE journal_entries SET visibility = ?2, review_status = ?3 WHERE id = ?1`,
  ).bind(entry.id, visibility, reviewStatus).run();
  if (visibility === "PUBLISHED") return `Published journal **${entry.id.slice(0, 8)}** ✅\n${JOURNAL_URL}`;
  return `Journal **${entry.id.slice(0, 8)}** is PRIVATE again ✅`;
}

async function buildLogin(interaction, env) {
  const access = await syncEntitlement(interaction, env);
  const link = await createMemberLoginLink({
    userId: invokingUserId(interaction),
    guildId: interaction.guild_id || null,
    canManageJournal: canManage(interaction),
  }, env);
  return [
    `🔐 **SIGNAL BRIDGE | ${access.tier} ACCESS**`,
    "Open your private Signal Bridge workspace: journal history, screenshots, and Strategy Lab.",
    link,
    "This one-time link expires in 10 minutes. After sign-in, the browser session lasts 24 hours.",
  ].join("\n");
}

function friendlyError(error) {
  const code = String(error?.message || "member_command_failed");
  const messages = {
    journal_storage_not_configured: "Journal storage is not ready on Signal Bridge yet.",
    discord_user_missing: "Discord did not provide a user identity for this command.",
    journal_id_too_short: "Use at least 6 characters of the journal ID.",
    journal_not_found: "I could not find that journal record under your Discord account.",
    journal_id_ambiguous: "That journal ID prefix matches more than one record. Use more of the ID.",
    journal_update_empty: "Add at least one field to update: result, P&L, R, or review note.",
    journal_update_invalid_number: "P&L and R must be valid numbers.",
    manager_permission_required: "Publishing controls are limited to server managers during beta.",
    member_storage_not_configured: "Private member storage is not ready yet.",
    premium_role_required: "Your Discord account does not currently have the Signal Bridge Premium role.",
  };
  return { code, message: messages[code] || "Signal Bridge hit a backend error on that command. The failure was logged for review." };
}

async function perform(interaction, command, env) {
  if (command === "start") return buildStartGuide();
  if (command === "journal-inbox") return listJournalForUser(interaction, env);
  if (command === "journal-update") return updateOwnJournal(interaction, env);
  if (command === "journal-publish") return setJournalVisibility(interaction, "PUBLISHED", env);
  if (command === "journal-private") return setJournalVisibility(interaction, "PRIVATE", env);
  if (command === "journal-login" || command === "member-login") return buildLogin(interaction, env);
  throw new Error("unknown_member_command");
}

async function completeDeferred(interaction, command, env) {
  const log = await logStart(interaction, command, env);
  try {
    const content = await perform(interaction, command, env);
    await editOriginal(interaction, content);
    await logFinish(log, "SUCCESS", null, env);
  } catch (error) {
    const friendly = friendlyError(error);
    try { await editOriginal(interaction, friendly.message); } catch { /* no-op */ }
    await logFinish(log, "FAILED", friendly.code, env);
    console.error(`Signal Bridge deferred Discord command failed: ${command} · ${friendly.code}`);
  }
}

export async function handleDiscordMemberInteraction(request, env, ctx) {
  if (request.method !== "POST") return jsonResponse({ ok: false, error: "method_not_allowed" }, 405);
  if (!env.DISCORD_PUBLIC_KEY) return jsonResponse({ ok: false, error: "discord_interactions_not_configured" }, 503);

  const verified = await verifyDiscordSignature(request, env.DISCORD_PUBLIC_KEY);
  if (!verified.ok) return jsonResponse({ ok: false, error: "invalid_discord_signature" }, 401);

  let interaction;
  try { interaction = JSON.parse(verified.bodyText); }
  catch { return jsonResponse({ ok: false, error: "invalid_json" }, 400); }

  if (interaction.type !== INTERACTION_APPLICATION_COMMAND) {
    return jsonResponse({ type: 4, data: { content: "Unsupported Signal Bridge interaction.", flags: MESSAGE_EPHEMERAL } });
  }
  if (env.DISCORD_APPLICATION_ID && interaction.application_id !== env.DISCORD_APPLICATION_ID) {
    return jsonResponse({ type: 4, data: { content: "This interaction belongs to a different Discord app.", flags: MESSAGE_EPHEMERAL } });
  }
  if (env.DISCORD_GUILD_ID && interaction.guild_id !== env.DISCORD_GUILD_ID) {
    return jsonResponse({ type: 4, data: { content: "Signal Bridge member tools are only enabled in the configured server.", flags: MESSAGE_EPHEMERAL } });
  }

  const command = compact(interaction?.data?.name, 64).toLowerCase();
  if (!MEMBER_COMMANDS.has(command)) {
    return jsonResponse({ type: 4, data: { content: "Unknown Signal Bridge member command.", flags: MESSAGE_EPHEMERAL } });
  }

  const task = completeDeferred(interaction, command, env);
  if (ctx?.waitUntil) ctx.waitUntil(task);
  else task.catch((error) => console.error(error));
  return deferEphemeral();
}
