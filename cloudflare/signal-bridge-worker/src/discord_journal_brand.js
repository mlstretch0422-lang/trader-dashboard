const JOURNAL_COMMANDS = new Set([
  "journal",
  "capture to journal",
  "publish to journal",
  "journal-inbox",
  "journal-publish",
  "journal-private",
]);

const STYLE = {
  "journal": { title: "SIGNAL BRIDGE · TRADE JOURNAL", color: 0x5ce0aa },
  "capture to journal": { title: "SIGNAL BRIDGE · JOURNAL CAPTURE", color: 0x61c3ff },
  "publish to journal": { title: "SIGNAL BRIDGE · JOURNAL PUBLISH", color: 0xa287ff },
  "journal-inbox": { title: "SIGNAL BRIDGE · JOURNAL INBOX", color: 0x61c3ff },
  "journal-publish": { title: "SIGNAL BRIDGE · JOURNAL PUBLISH", color: 0xa287ff },
  "journal-private": { title: "SIGNAL BRIDGE · JOURNAL PRIVACY", color: 0xe5b95f },
};

function cleanDescription(value) {
  return String(value || "")
    .replace(/^\s*[📡📝📚]\s*\*\*SIGNAL BRIDGE\s*[|·][^\n]*\*\*\s*/i, "")
    .trim()
    .slice(0, 3900);
}

function isErrorLike(text) {
  const value = String(text || "").toLowerCase();
  return value.includes("could not") ||
    value.includes("required") ||
    value.includes("limited to") ||
    value.includes("already captured") ||
    value.includes("unsupported") ||
    value.includes("unknown signal bridge");
}

export async function brandJournalInteractionResponse(response, commandName) {
  const command = String(commandName || "").toLowerCase();
  if (!JOURNAL_COMMANDS.has(command) || !response?.ok) return response;

  let body;
  try {
    body = await response.clone().json();
  } catch {
    return response;
  }

  const data = body?.data;
  if (body?.type !== 4 || !data || data.embeds?.length || !data.content) return response;

  const original = String(data.content);
  const style = STYLE[command] || STYLE.journal;
  const error = isErrorLike(original);
  const description = cleanDescription(original) || "Journal action completed.";
  const title = error ? "SIGNAL BRIDGE · JOURNAL ACTION" : style.title;
  const color = error ? 0xfb7185 : style.color;

  const next = {
    ...body,
    data: {
      ...data,
      content: "",
      embeds: [{
        title,
        description,
        color,
        footer: { text: "Signal Bridge · trade journal" },
        timestamp: new Date().toISOString(),
      }],
      allowed_mentions: { parse: [] },
    },
  };

  return new Response(JSON.stringify(next), {
    status: response.status,
    headers: response.headers,
  });
}
