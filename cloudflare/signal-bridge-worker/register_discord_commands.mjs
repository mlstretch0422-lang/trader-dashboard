const token = process.env.DISCORD_BOT_TOKEN;
const applicationId = process.env.DISCORD_APPLICATION_ID;
const guildId = process.env.DISCORD_GUILD_ID;

if (!token) throw new Error("DISCORD_BOT_TOKEN is required");
if (!applicationId) throw new Error("DISCORD_APPLICATION_ID is required");
if (!guildId) throw new Error("DISCORD_GUILD_ID is required");

const MANAGE_GUILD_PERMISSION = "32";

const symbolOption = {
  name: "symbol",
  description: "Market symbol (defaults to MES)",
  type: 3,
  required: false,
  max_length: 32,
};

const resultChoices = [
  { name: "Win", value: "WIN" },
  { name: "Loss", value: "LOSS" },
  { name: "Break even", value: "BE" },
  { name: "Open", value: "OPEN" },
  { name: "Pass / no trade", value: "PASS" },
  { name: "Not assigned", value: "NA" },
];

const commands = [
  {
    name: "start",
    type: 1,
    description: "Start here: learn the Signal Bridge trading workflow",
    integration_types: [0],
    contexts: [0],
  },
  {
    name: "status",
    type: 1,
    description: "Check hosted Signal Bridge services and live data state",
    integration_types: [0],
    contexts: [0],
  },
  {
    name: "orb",
    type: 1,
    description: "Read the latest stored opening range and session lifecycle",
    integration_types: [0],
    contexts: [0],
    options: [symbolOption],
  },
  {
    name: "brief",
    type: 1,
    description: "Get the current Session Story and setup readiness",
    integration_types: [0],
    contexts: [0],
    options: [symbolOption],
  },
  {
    name: "news",
    type: 1,
    description: "Get high-impact calendar state and recent market headlines",
    integration_types: [0],
    contexts: [0],
    options: [
      {
        name: "refresh",
        description: "Refresh hosted market intelligence before replying",
        type: 5,
        required: false,
      },
    ],
  },
  {
    name: "member-login",
    type: 1,
    description: "Open your private Signal Bridge Premium workspace",
    integration_types: [0],
    contexts: [0],
  },
  {
    name: "journal",
    type: 1,
    description: "Save a trade, idea, or no-trade record to Signal Bridge",
    integration_types: [0],
    contexts: [0],
    options: [
      { name: "note", description: "What did you see, do, or want to test? Include the idea source if relevant.", type: 3, required: true, max_length: 2000 },
      { name: "symbol", description: "Market symbol, for example MES", type: 3, required: false, max_length: 32 },
      {
        name: "side",
        description: "Trade direction or no-trade state",
        type: 3,
        required: false,
        choices: [
          { name: "Long", value: "LONG" },
          { name: "Short", value: "SHORT" },
          { name: "Wait / no trade", value: "WAIT" },
        ],
      },
      { name: "result", description: "Use Open before exit, or enter the final result if already finished", type: 3, required: false, choices: resultChoices },
      { name: "setup", description: "Setup name, for example ORB retest", type: 3, required: false, max_length: 96 },
      { name: "strategy", description: "Strategy or model version", type: 3, required: false, max_length: 96 },
      { name: "pnl", description: "Dollar P&L if known", type: 10, required: false },
      { name: "rr", description: "R multiple if known", type: 10, required: false },
      { name: "chart", description: "Optional chart or execution screenshot", type: 11, required: false },
      { name: "publish", description: "Publish this entry to the website (server managers only)", type: 5, required: false },
    ],
  },
  {
    name: "journal-update",
    type: 1,
    description: "Close out or review one of your saved journal records",
    integration_types: [0],
    contexts: [0],
    options: [
      { name: "id", description: "Journal ID or unique ID prefix", type: 3, required: true, min_length: 6, max_length: 64 },
      { name: "result", description: "Final or current trade result", type: 3, required: false, choices: resultChoices },
      { name: "pnl", description: "Dollar P&L", type: 10, required: false },
      { name: "rr", description: "R multiple", type: 10, required: false },
      { name: "review", description: "Post-trade lesson or review note", type: 3, required: false, max_length: 1000 },
    ],
  },
  {
    name: "journal-inbox",
    type: 1,
    description: "Review your recent Signal Bridge journal records",
    integration_types: [0],
    contexts: [0],
    options: [
      {
        name: "status",
        description: "Which records to show",
        type: 3,
        required: false,
        choices: [
          { name: "Private", value: "PRIVATE" },
          { name: "Published", value: "PUBLISHED" },
          { name: "All", value: "ALL" },
        ],
      },
      {
        name: "limit",
        description: "Number of recent records to show (1-5)",
        type: 4,
        required: false,
        min_value: 1,
        max_value: 5,
      },
    ],
  },
  {
    name: "journal-publish",
    type: 1,
    description: "Publish a stored journal record by ID",
    default_member_permissions: MANAGE_GUILD_PERMISSION,
    integration_types: [0],
    contexts: [0],
    options: [
      { name: "id", description: "Journal ID or unique ID prefix", type: 3, required: true, min_length: 6, max_length: 64 },
    ],
  },
  {
    name: "journal-private",
    type: 1,
    description: "Move a published journal record back to private",
    default_member_permissions: MANAGE_GUILD_PERMISSION,
    integration_types: [0],
    contexts: [0],
    options: [
      { name: "id", description: "Journal ID or unique ID prefix", type: 3, required: true, min_length: 6, max_length: 64 },
    ],
  },
  {
    name: "Capture to Journal",
    type: 3,
    integration_types: [0],
    contexts: [0],
  },
  {
    name: "Publish to Journal",
    type: 3,
    default_member_permissions: MANAGE_GUILD_PERMISSION,
    integration_types: [0],
    contexts: [0],
  },
];

const endpoint = `https://discord.com/api/v10/applications/${applicationId}/guilds/${guildId}/commands`;
const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

async function bulkOverwriteGuildCommands(maxAttempts = 4) {
  for (let attempt = 1; attempt <= maxAttempts; attempt += 1) {
    const response = await fetch(endpoint, {
      method: "PUT",
      headers: {
        authorization: `Bot ${token}`,
        "content-type": "application/json",
        "user-agent": "SignalBridgeCommandRegistrar/2.1",
      },
      body: JSON.stringify(commands),
    });

    const payload = await response.json().catch(() => ({}));
    if (response.ok) {
      if (!Array.isArray(payload)) throw new Error("Discord returned an unexpected command payload.");
      return payload;
    }

    if (response.status === 429 && attempt < maxAttempts) {
      const retrySeconds = Number(payload?.retry_after ?? response.headers.get("retry-after") ?? 1);
      const waitMs = Math.max(1000, Math.ceil((Number.isFinite(retrySeconds) ? retrySeconds : 1) * 1000) + 250);
      console.warn(`Discord rate limited command sync. Retrying in ${waitMs} ms (${attempt}/${maxAttempts}).`);
      await sleep(waitMs);
      continue;
    }

    console.error(`Failed to bulk-register Signal Bridge commands: HTTP ${response.status}`);
    console.error(JSON.stringify(payload, null, 2));
    process.exitCode = 1;
    return null;
  }
  return null;
}

const registered = await bulkOverwriteGuildCommands();

if (registered) {
  const names = registered.map((command) => command.name).sort((a, b) => a.localeCompare(b));
  console.log(`Signal Bridge Discord command set synced (${registered.length} commands).`);
  for (const name of names) console.log(`  ✓ ${name}`);
}
