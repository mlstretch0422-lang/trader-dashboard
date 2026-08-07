const INTERACTION_PING = 1;
const INTERACTION_APPLICATION_COMMAND = 2;
const RESPONSE_PONG = 1;
const RESPONSE_CHANNEL_MESSAGE = 4;
const MESSAGE_EPHEMERAL = 1 << 6;

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
  if (!publicKeyHex || !signatureHex || !timestamp) {
    return { ok: false, bodyText: "" };
  }

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
  const lines = ["📝 **SIGNAL BRIDGE | JOURNAL SAVED**"];
  const identity = [record.symbol, record.side, record.result].filter(Boolean).join(" | ");
  if (identity) lines.push(identity);
  if (record.setup) lines.push(`Setup: ${record.setup}`);
  if (record.rr !== null) lines.push(`R: ${record.rr}`);
  if (record.pnl !== null) lines.push(`P&L: ${record.pnl}`);
  lines.push(`Note: ${record.raw_text.slice(0, 700)}`);
  lines.push("Saved privately to Signal Bridge Journal Intelligence.");
  return lines.join("\n");
}

async function handleSlashJournal(interaction, env) {
  const options = optionMap(interaction);
  const note = compactText(options.note, 4000);
  if (!note) {
    return jsonResponse({
      type: RESPONSE_CHANNEL_MESSAGE,
      data: { content: "Journal note is required.", flags: MESSAGE_EPHEMERAL },
    });
  }

  const chartId = options.chart || null;
  const attachment = chartId ? interaction?.data?.resolved?.attachments?.[chartId] : null;
  const tags = ["discord", "trade-journal", "slash-command"];
  if (options.setup) tags.push(compactText(options.setup, 40).toLowerCase());

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
      attachment_id: chartId,
      attachment_filename: attachment?.filename || null,
    }),
    image_url: attachment?.url || null,
  });

  const stored = await insertDiscordJournal(record, env);
  if (!stored.inserted) {
    return jsonResponse({
      type: RESPONSE_CHANNEL_MESSAGE,
      data: { content: "That journal interaction was already captured.", flags: MESSAGE_EPHEMERAL },
    });
  }

  return jsonResponse({
    type: RESPONSE_CHANNEL_MESSAGE,
    data: {
      content: commandReceipt(record),
      allowed_mentions: { parse: [] },
    },
  });
}

async function handleMessageCapture(interaction, env) {
  const targetId = interaction?.data?.target_id;
  const targetMessage = targetId ? interaction?.data?.resolved?.messages?.[targetId] : null;
  if (!targetMessage) {
    return jsonResponse({
      type: RESPONSE_CHANNEL_MESSAGE,
      data: { content: "I could not resolve that Discord message.", flags: MESSAGE_EPHEMERAL },
    });
  }

  const rawText = compactText(targetMessage.content, 4000);
  const firstAttachment = Array.isArray(targetMessage.attachments)
    ? targetMessage.attachments[0]
    : Object.values(targetMessage.attachments || {})[0];
  const fallbackText = firstAttachment
    ? `[Attachment: ${firstAttachment.filename || "journal image"}]`
    : "";

  if (!rawText && !fallbackText) {
    return jsonResponse({
      type: RESPONSE_CHANNEL_MESSAGE,
      data: { content: "That message has no text or attachment to capture.", flags: MESSAGE_EPHEMERAL },
    });
  }

  const authorId = targetMessage?.author?.id || null;
  const record = baseRecord(interaction, {
    title: "Discord journal message",
    raw_text: rawText || fallbackText,
    tags: JSON.stringify(["discord", "trade-journal", "message-capture"]),
    source: "discord-message",
    source_ref: sourceRef(interaction, {
      command: "Capture to Journal",
      target_message_id: targetId,
      target_author_id: authorId,
      attachment_id: firstAttachment?.id || null,
      attachment_filename: firstAttachment?.filename || null,
    }),
    image_url: firstAttachment?.url || null,
    discord_message_id: targetId,
    discord_author_id: authorId,
  });

  const stored = await insertDiscordJournal(record, env);
  return jsonResponse({
    type: RESPONSE_CHANNEL_MESSAGE,
    data: {
      content: stored.inserted
        ? "Captured that trade-journal message privately into Signal Bridge ✅"
        : "That message is already in Signal Bridge Journal Intelligence.",
      flags: MESSAGE_EPHEMERAL,
      allowed_mentions: { parse: [] },
    },
  });
}

export async function handleDiscordInteraction(request, env) {
  if (request.method !== "POST") {
    return jsonResponse({ ok: false, error: "method_not_allowed" }, 405);
  }
  if (!env.DISCORD_PUBLIC_KEY) {
    return jsonResponse({ ok: false, error: "discord_interactions_not_configured" }, 503);
  }

  const verified = await verifyDiscordSignature(request, env.DISCORD_PUBLIC_KEY);
  if (!verified.ok) {
    return jsonResponse({ ok: false, error: "invalid_discord_signature" }, 401);
  }

  let interaction;
  try {
    interaction = JSON.parse(verified.bodyText);
  } catch {
    return jsonResponse({ ok: false, error: "invalid_json" }, 400);
  }

  if (interaction.type === INTERACTION_PING) {
    return jsonResponse({ type: RESPONSE_PONG });
  }

  if (interaction.type !== INTERACTION_APPLICATION_COMMAND) {
    return jsonResponse({
      type: RESPONSE_CHANNEL_MESSAGE,
      data: { content: "Unsupported Signal Bridge interaction.", flags: MESSAGE_EPHEMERAL },
    });
  }

  const location = allowedDiscordLocation(interaction, env);
  if (!location.ok) {
    return jsonResponse({
      type: RESPONSE_CHANNEL_MESSAGE,
      data: { content: location.message, flags: MESSAGE_EPHEMERAL },
    });
  }

  const commandName = compactText(interaction?.data?.name, 64).toLowerCase();
  try {
    if (commandName === "journal") {
      return await handleSlashJournal(interaction, env);
    }
    if (commandName === "capture to journal") {
      return await handleMessageCapture(interaction, env);
    }
  } catch (error) {
    console.error(`Signal Bridge Discord journal capture failed: ${error?.message || "CAPTURE_ERROR"}`);
    return jsonResponse({
      type: RESPONSE_CHANNEL_MESSAGE,
      data: {
        content: "Signal Bridge could not save that journal entry. Check the capture service and try again.",
        flags: MESSAGE_EPHEMERAL,
      },
    });
  }

  return jsonResponse({
    type: RESPONSE_CHANNEL_MESSAGE,
    data: { content: "Unknown Signal Bridge command.", flags: MESSAGE_EPHEMERAL },
  });
}
