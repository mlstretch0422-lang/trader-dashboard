const token = process.env.DISCORD_BOT_TOKEN;
const applicationId = process.env.DISCORD_APPLICATION_ID;
const guildId = process.env.DISCORD_GUILD_ID;

if (!token) throw new Error("DISCORD_BOT_TOKEN is required");
if (!applicationId) throw new Error("DISCORD_APPLICATION_ID is required");
if (!guildId) throw new Error("DISCORD_GUILD_ID is required");

const symbolOption = {
  name: "symbol",
  description: "Market symbol (defaults to MES)",
  type: 3,
  required: false,
  max_length: 32,
};

const commands = [
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
    description: "Save a trade or no-trade journal record to Signal Bridge",
    integration_types: [0],
    contexts: [0],
    options: [
      { name: "note", description: "What happened and what did you see?", type: 3, required: true, max_length: 2000 },
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
      {
        name: "result",
        description: "Current result",
        type: 3,
        required: false,
        choices: [
          { name: "Win", value: "WIN" },
          { name: "Loss", value: "LOSS" },
          { name: "Break even", value: "BE" },
          { name: "Open", value: "OPEN" },
          { name: "Pass / no trade", value: "PASS" },
          { name: "Not assigned", value: "NA" },
        ],
      },
      { name: "setup", description: "Setup name, for example ORB retest", type: 3, required: false, max_length: 96 },
      { name: "strategy", description: "Strategy or model version", type: 3, required: false, max_length: 96 },
      { name: "pnl", description: "Dollar P&L if known", type: 10, required: false },
      { name: "rr", description: "R multiple if known", type: 10, required: false },
      { name: "chart", description: "Optional chart or execution screenshot", type: 11, required: false },
      { name: "publish", description: "Publish this entry to the website (server managers only)", type: 5, required: false },
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
    name: "journal-login",
    type: 1,
    description: "Legacy alias for the private Signal Bridge workspace",
    integration_types: [0],
    contexts: [0],
  },
  {
    name: "journal-publish",
    type: 1,
    description: "Publish a stored journal record by ID (server managers only)",
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
    integration_types: [0],
    contexts: [0],
  },
];

const endpoint = `https://discord.com/api/v10/applications/${applicationId}/guilds/${guildId}/commands`;

for (const command of commands) {
  const response = await fetch(endpoint, {
    method: "POST",
    headers: {
      authorization: `Bot ${token}`,
      "content-type": "application/json",
    },
    body: JSON.stringify(command),
  });

  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    console.error(`Failed to register ${command.name}: HTTP ${response.status}`);
    console.error(JSON.stringify(payload, null, 2));
    process.exitCode = 1;
    continue;
  }
  console.log(`Registered ${command.name} (${payload.id || "ok"})`);
}

if (!process.exitCode) {
  console.log("Signal Bridge Discord commands are registered for this server.");
}
