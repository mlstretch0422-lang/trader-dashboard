const INTERACTION_PING = 1;
const INTERACTION_APPLICATION_COMMAND = 2;
const RESPONSE_PONG = 1;
const RESPONSE_CHANNEL_MESSAGE = 4;
const MESSAGE_EPHEMERAL = 1 << 6;
const PERMISSION_ADMINISTRATOR = 1n << 3n;
const PERMISSION_MANAGE_GUILD = 1n << 5n;
const JOURNAL_URL = "https://mlstretch0422-lang.github.io/trader-dashboard/journal.html";

function jsonResponse(body, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: {
      "content-type": "application/json; charset=utf-8",
      "cache-control": "no-store",
    },
  });
}

function hexToBytes(hex) {
  if (typeof hex !== "string" || hex.length % 2 !== 0 || !/^[0-9a-f]+$/i.test(hex)) {
    throw new Error("invalid_hex");
  }
  const bytes = new Uint8Array(hex.length / 2);
  for (let i = 0; i < hex.length; i += 2) {
    bytes[i / 2] = Number.parseInt(hex.slice(i, i + 2), 16);
  }
  return bytes;
}

async function verifyDiscordSignature(request, publicKeyHex) {
  const signatureHex = request.headers.get("x-signature-ed25519");
  const timestamp = request.headers.get("x-signature-timestamp");
  if (!publicKeyHex || !signatureHex || !timestamp) return { ok: false, bodyText: "" };

  const bodyText = await request.text();
  try {
    const publicKey = await crypto.subtle.importKey(
      "raw",
      hexToBytes(publicKeyHex),
      { name: "Ed25519" },
      false,
      ["verify"],
    );
    const data = new TextEncoder().encode(`${timestamp}${bodyText}`);
    const ok = await crypto.subtle.verify(
      { name: "Ed25519" },
      publicKey,
      hexToBytes(signatureHex),
      data,
    );
    return { ok, bodyText };
  } catch (error) {
    console.error(`Signal Bridge Discord signature verification failed: ${error?.message || "VERIFY_ERROR"}`);
    return { ok: false, bodyText };
  }
}

function optionMap(interaction) {
  const options = interaction?.data?.options || [];
  return Object.fromEntries(options.map((option) => [option.name, option.value]));
}

function invokingUserId(interaction) {
  return interaction?.member?.user?.id || interaction?.user?.id || null;
}

function canPublishJournal(interaction) {
  try {
    const permissions = BigInt(interaction?.member?.permissions || "0");
    return Boolean(permissions & PERMISSION_ADMINISTRATOR) || Boolean(permissions & PERMISSION_MANAGE_GUILD);
  } catch {
    return false;
  }
}

function allowedDiscordLocation(interaction, env) {
  if (env.DISCORD_APPLICATION_ID && interaction.application_id !== env.DISCORD_APPLICATION_ID) {
    return { ok: false, message: "This interaction belongs to a different Discord app." };
  }
  if (env.DISCORD_GUILD_ID && interaction.guild_id !== env.DISCORD_GUILD_ID) {
    return { ok: false, message: "Signal Bridge Journal is only enabled in the configured server." };
  }
  if (env.DISCORD_JOURNAL_CHANNEL_ID && interaction.channel_id !== env.DISCORD_JOURNAL_CHANNEL_ID) {
    return { ok: false, message: "Use this command in the configured trade-journal channel." };
  }
  return { ok: true };
}

function compactText(value, maxLength = 4000) {
  return String(value ?? "").trim().slice(0, maxLength);
}

function compactLine(value, maxLength = 120) {
  return compactText(value, maxLength).replace(/\s+/g, " ");
}

function nullableText(value, maxLength) {
  const text = compactText(value, maxLength);
  return text || null;
}

function nullableNumber(value) {
  if (value === null || value === undefined || value === "") return null;
  const number = Number(value);
  return Number.isFinite(number) ? number : null;
}

function sourceRef(interaction, extra = {}) {
  return JSON.stringify({
    discord_interaction_id: interaction.id,
    discord_application_id: interaction.application_id,
    discord_guild_id: interaction.guild_id || null,
    discord_channel_id: interaction.channel_id || null,
    invoked_by_user_id: invokingUserId(interaction),
    ...extra,
  });
}

function parseTags(value) {
  try { return JSON.parse(value || "[]"); } catch { return []; }
}

function normalizeDbEntry(entry) {
  return entry ? { ...entry, tags: parseTags(entry.tags) } : null;
}

async function insertDiscordJournal(record, env) {
  if (!env.DB) throw new Error("journal_storage_not_configured");

  const result = await env.DB.prepare(
    `INSERT OR IGNORE INTO journal_entries (
      id, created_at, journal_time, symbol, side, setup, strategy, title,
      raw_text, summary, result, pnl, rr, tags, source, source_ref,
      signal_event_id, image_url, visibility, review_status,
      discord_guild_id, discord_channel_id, discord_message_id,
      discord_author_id, discord_interaction_id
    ) VALUES (
      ?1, ?2, ?3, ?4, ?5, ?6, ?7, ?8, ?9, ?10,
      ?11, ?12, ?13, ?14, ?15, ?16, ?17, ?18, ?19, ?20,
      ?21, ?22, ?23, ?24, ?25
    )`,
  )
    .bind(
      record.id,
      record.created_at,
      record.journal_time,
      record.symbol,
      record.side,
      record.setup,
      record.strategy,
      record.title,
      record.raw_text,
      record.summary,
      record.result,
      record.pnl,
      record.rr,
      record.tags,
      record.source,
      record.source_ref,
      record.signal_event_id,
      record.image_url,
      record.visibility,
      record.review_status,
      record.discord_guild_id,
      record.discord_channel_id,
      record.discord_message_id,
      record.discord_author_id,
      record.discord_interaction_id,
    )
    .run();

  return { inserted: (result.meta?.changes ?? 0) > 0 };
}

async function getJournalByMessageId(messageId, env) {
  if (!env.DB || !messageId) return null;
  const result = await env.DB.prepare(
    `SELECT * FROM journal_entries WHERE discord_message_id = ?1 LIMIT 1`,
  ).bind(messageId).run();
  return normalizeDbEntry(Array.isArray(result.results) ? result.results[0] : null);
}

async function promoteDiscordMessage(targetMessageId, imageUrl, env) {
  if (!env.DB || !targetMessageId) return null;
  await env.DB.prepare(
    `UPDATE journal_entries
     SET visibility = 'PUBLISHED',
         review_status = 'REVIEWED',
         image_url = COALESCE(image_url, ?2)
     WHERE discord_message_id = ?1`,
  ).bind(targetMessageId, imageUrl || null).run();
  return getJournalByMessageId(targetMessageId, env);
}

async function findJournalByIdPrefix(idValue, env) {
  if (!env.DB) throw new Error("journal_storage_not_configured");
  const id = compactText(idValue, 64);
  if (id.length < 6) throw new Error("journal_id_too_short");

  const exact = await env.DB.prepare(`SELECT * FROM journal_entries WHERE id = ?1 LIMIT 1`).bind(id).run();
  const exactEntry = Array.isArray(exact.results) ? exact.results[0] : null;
  if (exactEntry) return normalizeDbEntry(exactEntry);

  const prefix = await env.DB.prepare(
    `SELECT * FROM journal_entries WHERE id LIKE ?1 ORDER BY created_at DESC LIMIT 2`,
  ).bind(`${id}%`).run();
  const matches = Array.isArray(prefix.results) ? prefix.results : [];
  if (!matches.length) throw new Error("journal_not_found");
  if (matches.length > 1) throw new Error("journal_id_ambiguous");
  return normalizeDbEntry(matches[0]);
}

async function setJournalVisibility(idValue, visibility, env) {
  const entry = await findJournalByIdPrefix(idValue, env);
  const reviewStatus = visibility === "PUBLISHED" ? "REVIEWED" : entry.review_status;
  await env.DB.prepare(
    `UPDATE journal_entries SET visibility = ?2, review_status = ?3 WHERE id = ?1`,
  ).bind(entry.id, visibility, reviewStatus).run();
  return findJournalByIdPrefix(entry.id, env);
}

async function listJournalForUser(userId, visibility, limit, env) {
  if (!env.DB) throw new Error("journal_storage_not_configured");
  if (!userId) throw new Error("discord_user_missing");
  const values = [userId];
  let where = "discord_author_id = ?1";
  if (visibility && visibility !== "ALL") {
    values.push(visibility);
    where += ` AND visibility = ?${values.length}`;
  }
  values.push(limit);
  const result = await env.DB.prepare(
    `SELECT * FROM journal_entries
     WHERE ${where}
     ORDER BY COALESCE(journal_time, created_at) DESC
     LIMIT ?${values.length}`,
  ).bind(...values).run();
  return (Array.isArray(result.results) ? result.results : []).map(normalizeDbEntry);
}

function baseRecord(interaction, overrides) {
  const now = new Date().toISOString();
  return {
    id: crypto.randomUUID(),
    created_at: now,
    journal_time: now,
    symbol: null,
    side: null,
    setup: null,
    strategy: null,
    title: null,
    raw_text: "",
    summary: null,
    result: "NA",
    pnl: null,
    rr: null,
    tags: JSON.stringify(["discord", "trade-journal"]),
    source: "discord",
    source_ref: sourceRef(interaction),
    signal_event_id: null,
    image_url: null,
    visibility: "PRIVATE",
    review_status: "RAW",
    discord_guild_id: interaction.guild_id || null,
    discord_channel_id: interaction.channel_id || null,
    discord_message_id: null,
    discord_author_id: invokingUserId(interaction),
    discord_interaction_id: interaction.id,
    ...overrides,
  };
}

function commandReceipt(record) {
  const published = record.visibility === "PUBLISHED";
  const lines = [published ? "📡 **SIGNAL BRIDGE | JOURNAL PUBLISHED**" : "📝 **SIGNAL BRIDGE | JOURNAL SAVED**"];
  const identity = [record.symbol, record.side, record.result].filter(Boolean).join(" | ");
  if (identity) lines.push(identity);
  if (record.setup) lines.push(`Setup: ${record.setup}`);
  if (record.rr !== null) lines.push(`R: ${record.rr}`);
  if (record.pnl !== null) lines.push(`P&L: ${record.pnl}`);
  lines.push(`ID: ${record.id.slice(0, 8)}`);
  lines.push(`Note: ${record.raw_text.slice(0, 650)}`);
  lines.push(published
    ? `Published: ${JOURNAL_URL}`
    : "Saved privately. Use /journal-inbox to review it later.");
  return lines.join("\n");
}

async function handleSlashJournal(interaction, env) {
  const options = optionMap(interaction);
  const note = compactText(options.note, 4000);
  if (!note) {
    return jsonResponse({ type: RESPONSE_CHANNEL_MESSAGE, data: { content: "Journal note is required.", flags: MESSAGE_EPHEMERAL } });
  }

  const publishRequested = options.publish === true;
  if (publishRequested && !canPublishJournal(interaction)) {
    return jsonResponse({
      type: RESPONSE_CHANNEL_MESSAGE,
      data: {
        content: "Publishing to the public Journal is limited to server managers. Re-run without Publish to save privately.",
        flags: MESSAGE_EPHEMERAL,
      },
    });
  }

  const chartId = options.chart || null;
  const attachment = chartId ? interaction?.data?.resolved?.attachments?.[chartId] : null;
  const tags = ["discord", "trade-journal", "slash-command"];
  if (options.setup) tags.push(compactText(options.setup, 40).toLowerCase());
  if (publishRequested) tags.push("published");

  const record = baseRecord(interaction, {
    symbol: nullableText(options.symbol, 32)?.toUpperCase() || null,
    side: nullableText(options.side, 16)?.toUpperCase() || null,
    setup: nullableText(options.setup, 96),
    strategy: nullableText(options.strategy, 96),
    title: "Discord trade journal",
    raw_text: note,
    result: nullableText(options.result, 16)?.toUpperCase() || "NA",
    pnl: nullableNumber(options.pnl),
    rr: nullableNumber(options.rr),
    tags: JSON.stringify(tags),
    source: "discord-slash",
    source_ref: sourceRef(interaction, {
      command: "journal",
      publish_requested: publishRequested,
      attachment_id: chartId,
      attachment_filename: attachment?.filename || null,
    }),
    image_url: attachment?.url || null,
    visibility: publishRequested ? "PUBLISHED" : "PRIVATE",
    review_status: publishRequested ? "REVIEWED" : "RAW",
  });

  const stored = await insertDiscordJournal(record, env);
  if (!stored.inserted) {
    return jsonResponse({ type: RESPONSE_CHANNEL_MESSAGE, data: { content: "That journal interaction was already captured.", flags: MESSAGE_EPHEMERAL } });
  }

  return jsonResponse({
    type: RESPONSE_CHANNEL_MESSAGE,
    data: { content: commandReceipt(record), allowed_mentions: { parse: [] } },
  });
}

async function handleMessageCapture(interaction, env, publish = false) {
  if (publish && !canPublishJournal(interaction)) {
    return jsonResponse({
      type: RESPONSE_CHANNEL_MESSAGE,
      data: { content: "Publishing to the public Journal is limited to server managers.", flags: MESSAGE_EPHEMERAL },
    });
  }

  const targetId = interaction?.data?.target_id;
  const targetMessage = targetId ? interaction?.data?.resolved?.messages?.[targetId] : null;
  if (!targetMessage) {
    return jsonResponse({ type: RESPONSE_CHANNEL_MESSAGE, data: { content: "I could not resolve that Discord message.", flags: MESSAGE_EPHEMERAL } });
  }

  const rawText = compactText(targetMessage.content, 4000);
  const firstAttachment = Array.isArray(targetMessage.attachments)
    ? targetMessage.attachments[0]
    : Object.values(targetMessage.attachments || {})[0];
  const fallbackText = firstAttachment ? `[Attachment: ${firstAttachment.filename || "journal image"}]` : "";

  if (!rawText && !fallbackText) {
    return jsonResponse({ type: RESPONSE_CHANNEL_MESSAGE, data: { content: "That message has no text or attachment to capture.", flags: MESSAGE_EPHEMERAL } });
  }

  if (publish) {
    const promoted = await promoteDiscordMessage(targetId, firstAttachment?.url || null, env);
    if (promoted?.visibility === "PUBLISHED") {
      return jsonResponse({
        type: RESPONSE_CHANNEL_MESSAGE,
        data: {
          content: `Published journal ${promoted.id.slice(0, 8)} to the website ✅\n${JOURNAL_URL}`,
          flags: MESSAGE_EPHEMERAL,
          allowed_mentions: { parse: [] },
        },
      });
    }
  }

  const authorId = targetMessage?.author?.id || null;
  const record = baseRecord(interaction, {
    title: publish ? "Published Discord journal message" : "Discord journal message",
    raw_text: rawText || fallbackText,
    tags: JSON.stringify(["discord", "trade-journal", "message-capture", ...(publish ? ["published"] : [])]),
    source: publish ? "discord-publish" : "discord-message",
    source_ref: sourceRef(interaction, {
      command: publish ? "Publish to Journal" : "Capture to Journal",
      target_message_id: targetId,
      target_author_id: authorId,
      attachment_id: firstAttachment?.id || null,
      attachment_filename: firstAttachment?.filename || null,
    }),
    image_url: firstAttachment?.url || null,
    visibility: publish ? "PUBLISHED" : "PRIVATE",
    review_status: publish ? "REVIEWED" : "RAW",
    discord_message_id: targetId,
    discord_author_id: authorId,
  });

  const stored = await insertDiscordJournal(record, env);
  return jsonResponse({
    type: RESPONSE_CHANNEL_MESSAGE,
    data: {
      content: stored.inserted
        ? (publish
          ? `Published journal ${record.id.slice(0, 8)} to Signal Bridge ✅\n${JOURNAL_URL}`
          : `Captured privately as journal ${record.id.slice(0, 8)} ✅\nUse /journal-inbox to review it.`)
        : "That Discord message is already stored. Use /journal-inbox to find its journal ID.",
      flags: MESSAGE_EPHEMERAL,
      allowed_mentions: { parse: [] },
    },
  });
}

async function handleJournalInbox(interaction, env) {
  const options = optionMap(interaction);
  const requestedLimit = Number(options.limit || 5);
  const limit = Number.isFinite(requestedLimit) ? Math.min(Math.max(Math.trunc(requestedLimit), 1), 5) : 5;
  const status = compactText(options.status || "PRIVATE", 16).toUpperCase();
  const visibility = ["PRIVATE", "PUBLISHED", "ALL"].includes(status) ? status : "PRIVATE";
  const entries = await listJournalForUser(invokingUserId(interaction), visibility, limit, env);

  if (!entries.length) {
    return jsonResponse({
      type: RESPONSE_CHANNEL_MESSAGE,
      data: { content: `No ${visibility.toLowerCase()} journal records found for your Discord account.`, flags: MESSAGE_EPHEMERAL },
    });
  }

  const lines = [`📚 **SIGNAL BRIDGE | YOUR JOURNAL INBOX**`, `${visibility} · ${entries.length} record${entries.length === 1 ? "" : "s"}`];
  for (const entry of entries) {
    const identity = [entry.symbol, entry.side, entry.result].filter(Boolean).join(" | ") || "Unclassified";
    lines.push("");
    lines.push(`**${entry.id.slice(0, 8)}** · ${entry.visibility} · ${identity}`);
    if (entry.setup) lines.push(`Setup: ${compactLine(entry.setup, 60)}`);
    lines.push(compactLine(entry.summary || entry.raw_text, 120));
    if (entry.image_url) lines.push(`Chart: ${entry.image_url}`);
  }
  lines.push("");
  lines.push("Server managers can publish a stored record with `/journal-publish id:<ID>`. ");

  return jsonResponse({
    type: RESPONSE_CHANNEL_MESSAGE,
    data: { content: lines.join("\n").slice(0, 1950), flags: MESSAGE_EPHEMERAL, allowed_mentions: { parse: [] } },
  });
}

async function handleJournalPublishById(interaction, env, visibility) {
  if (!canPublishJournal(interaction)) {
    return jsonResponse({
      type: RESPONSE_CHANNEL_MESSAGE,
      data: { content: "Journal publishing controls are limited to server managers.", flags: MESSAGE_EPHEMERAL },
    });
  }
  const options = optionMap(interaction);
  const id = compactText(options.id, 64);
  if (!id) {
    return jsonResponse({ type: RESPONSE_CHANNEL_MESSAGE, data: { content: "A journal ID is required.", flags: MESSAGE_EPHEMERAL } });
  }
  const entry = await setJournalVisibility(id, visibility, env);
  const message = visibility === "PUBLISHED"
    ? `Published journal ${entry.id.slice(0, 8)} ✅\n${JOURNAL_URL}`
    : `Moved journal ${entry.id.slice(0, 8)} back to PRIVATE ✅`;
  return jsonResponse({
    type: RESPONSE_CHANNEL_MESSAGE,
    data: { content: message, flags: MESSAGE_EPHEMERAL, allowed_mentions: { parse: [] } },
  });
}

function friendlyError(error) {
  const reason = String(error?.message || "journal_error");
  const messages = {
    journal_not_found: "I could not find that journal ID.",
    journal_id_ambiguous: "That ID prefix matches more than one journal record. Use more characters from the ID.",
    journal_id_too_short: "Use at least 6 characters of the journal ID.",
    journal_storage_not_configured: "Journal storage is not configured on the Worker.",
  };
  return messages[reason] || "Signal Bridge could not complete that journal action.";
}

export async function handleDiscordInteraction(request, env) {
  if (request.method !== "POST") return jsonResponse({ ok: false, error: "method_not_allowed" }, 405);
  if (!env.DISCORD_PUBLIC_KEY) return jsonResponse({ ok: false, error: "discord_interactions_not_configured" }, 503);

  const verified = await verifyDiscordSignature(request, env.DISCORD_PUBLIC_KEY);
  if (!verified.ok) return jsonResponse({ ok: false, error: "invalid_discord_signature" }, 401);

  let interaction;
  try {
    interaction = JSON.parse(verified.bodyText);
  } catch {
    return jsonResponse({ ok: false, error: "invalid_json" }, 400);
  }

  if (interaction.type === INTERACTION_PING) return jsonResponse({ type: RESPONSE_PONG });
  if (interaction.type !== INTERACTION_APPLICATION_COMMAND) {
    return jsonResponse({ type: RESPONSE_CHANNEL_MESSAGE, data: { content: "Unsupported Signal Bridge interaction.", flags: MESSAGE_EPHEMERAL } });
  }

  const location = allowedDiscordLocation(interaction, env);
  if (!location.ok) {
    return jsonResponse({ type: RESPONSE_CHANNEL_MESSAGE, data: { content: location.message, flags: MESSAGE_EPHEMERAL } });
  }

  const commandName = compactText(interaction?.data?.name, 64).toLowerCase();
  try {
    if (commandName === "journal") return await handleSlashJournal(interaction, env);
    if (commandName === "capture to journal") return await handleMessageCapture(interaction, env, false);
    if (commandName === "publish to journal") return await handleMessageCapture(interaction, env, true);
    if (commandName === "journal-inbox") return await handleJournalInbox(interaction, env);
    if (commandName === "journal-publish") return await handleJournalPublishById(interaction, env, "PUBLISHED");
    if (commandName === "journal-private") return await handleJournalPublishById(interaction, env, "PRIVATE");
  } catch (error) {
    console.error(`Signal Bridge Discord journal action failed: ${error?.message || "JOURNAL_ERROR"}`);
    return jsonResponse({
      type: RESPONSE_CHANNEL_MESSAGE,
      data: { content: friendlyError(error), flags: MESSAGE_EPHEMERAL },
    });
  }

  return jsonResponse({
    type: RESPONSE_CHANNEL_MESSAGE,
    data: { content: "Unknown Signal Bridge command.", flags: MESSAGE_EPHEMERAL },
  });
}
