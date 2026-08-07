const MAX_BODY_BYTES = 32 * 1024;
const EVIDENCE_STAGES = new Set([
  "PROJECT_RULE",
  "IMPLEMENTED",
  "BACKTESTED",
  "ISOLATED_ATTRIBUTION",
  "WALK_FORWARD",
  "PAPER_FORWARD",
  "LIVE",
]);

function json(body, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: {
      "content-type": "application/json; charset=utf-8",
      "cache-control": "no-store",
    },
  });
}

function text(value, max = 500) {
  return String(value ?? "").trim().slice(0, max);
}

function bearer(request) {
  const auth = request.headers.get("authorization") || "";
  return auth.startsWith("Bearer ") ? auth.slice(7) : "";
}

function authorized(request, env) {
  const expected = env.JOURNAL_ADMIN_TOKEN || env.SIGNAL_BRIDGE_TEST_TOKEN;
  return Boolean(expected) && bearer(request) === expected;
}

async function readJson(request) {
  const length = Number(request.headers.get("content-length") || 0);
  if (length > MAX_BODY_BYTES) throw new Error("body_too_large");
  const raw = await request.text();
  if (new TextEncoder().encode(raw).byteLength > MAX_BODY_BYTES) throw new Error("body_too_large");
  return JSON.parse(raw || "{}");
}

function jsonString(value, fallback = {}) {
  if (value === undefined || value === null || value === "") return JSON.stringify(fallback);
  if (typeof value === "string") {
    JSON.parse(value);
    return value;
  }
  return JSON.stringify(value);
}

async function profileExists(env, id) {
  const result = await env.DB.prepare("SELECT id FROM strategy_profiles WHERE id = ?1 LIMIT 1").bind(id).run();
  return Boolean(result.results?.[0]?.id);
}

async function versionExists(env, id) {
  const result = await env.DB.prepare("SELECT id FROM strategy_versions WHERE id = ?1 LIMIT 1").bind(id).run();
  return Boolean(result.results?.[0]?.id);
}

async function listStrategies(env) {
  const result = await env.DB.prepare(
    `SELECT p.id, p.created_at, p.updated_at, p.owner_type, p.owner_discord_id,
            p.slug, p.name, p.description, p.status,
            v.id AS current_version_id, v.version_label AS current_version_label,
            v.status AS current_version_status, v.evidence_stage AS current_evidence_stage,
            v.indicator_name, v.indicator_version
     FROM strategy_profiles p
     LEFT JOIN strategy_versions v ON v.strategy_id = p.id AND v.is_current = 1
     ORDER BY p.updated_at DESC`,
  ).run();
  return Array.isArray(result.results) ? result.results : [];
}

async function strategyDetail(env, strategyId) {
  const profileResult = await env.DB.prepare("SELECT * FROM strategy_profiles WHERE id = ?1 LIMIT 1").bind(strategyId).run();
  const profile = profileResult.results?.[0] || null;
  if (!profile) return null;

  const versionsResult = await env.DB.prepare(
    `SELECT * FROM strategy_versions WHERE strategy_id = ?1 ORDER BY created_at DESC`,
  ).bind(strategyId).run();
  const versions = Array.isArray(versionsResult.results) ? versionsResult.results : [];
  const versionIds = versions.map((row) => row.id);
  let observations = [];
  if (versionIds.length) {
    const placeholders = versionIds.map((_, index) => `?${index + 1}`).join(",");
    const obsResult = await env.DB.prepare(
      `SELECT * FROM strategy_observations
       WHERE strategy_version_id IN (${placeholders})
       ORDER BY created_at DESC LIMIT 200`,
    ).bind(...versionIds).run();
    observations = Array.isArray(obsResult.results) ? obsResult.results : [];
  }
  return { profile, versions, observations };
}

async function upsertProfile(env, body) {
  const id = text(body.id || crypto.randomUUID(), 96);
  const slug = text(body.slug, 96).toLowerCase();
  const name = text(body.name, 160);
  if (!slug || !name) throw new Error("profile_slug_and_name_required");
  const now = new Date().toISOString();
  const ownerType = text(body.owner_type || "SYSTEM", 24).toUpperCase();
  const ownerDiscordId = text(body.owner_discord_id, 64) || null;
  const description = text(body.description, 1200) || null;
  const status = text(body.status || "ACTIVE", 32).toUpperCase();

  await env.DB.prepare(
    `INSERT INTO strategy_profiles (
       id, created_at, updated_at, owner_type, owner_discord_id, slug, name, description, status
     ) VALUES (?1, ?2, ?2, ?3, ?4, ?5, ?6, ?7, ?8)
     ON CONFLICT(id) DO UPDATE SET
       updated_at = excluded.updated_at,
       owner_type = excluded.owner_type,
       owner_discord_id = excluded.owner_discord_id,
       slug = excluded.slug,
       name = excluded.name,
       description = excluded.description,
       status = excluded.status`,
  ).bind(id, now, ownerType, ownerDiscordId, slug, name, description, status).run();
  return { id, slug, name, status };
}

async function createVersion(env, body) {
  const strategyId = text(body.strategy_id, 96);
  if (!strategyId || !(await profileExists(env, strategyId))) throw new Error("strategy_not_found");
  const versionLabel = text(body.version_label, 120);
  if (!versionLabel) throw new Error("version_label_required");
  const id = text(body.id || crypto.randomUUID(), 128);
  const evidenceStage = text(body.evidence_stage || "IMPLEMENTED", 48).toUpperCase();
  if (!EVIDENCE_STAGES.has(evidenceStage)) throw new Error("invalid_evidence_stage");
  const status = text(body.status || "STAGED", 32).toUpperCase();
  const isCurrent = body.is_current === true || body.is_current === 1;
  const now = new Date().toISOString();
  const rulesJson = jsonString(body.rules, {});
  const configJson = jsonString(body.indicator_config, {});

  const statements = [];
  if (isCurrent) {
    statements.push(env.DB.prepare("UPDATE strategy_versions SET is_current = 0 WHERE strategy_id = ?1").bind(strategyId));
  }
  statements.push(env.DB.prepare(
    `INSERT INTO strategy_versions (
       id, strategy_id, version_label, created_at, status, evidence_stage,
       parent_version_id, rules_json, indicator_name, indicator_version,
       indicator_config_json, change_note, is_current
     ) VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7, ?8, ?9, ?10, ?11, ?12, ?13)`,
  ).bind(
    id,
    strategyId,
    versionLabel,
    now,
    status,
    evidenceStage,
    text(body.parent_version_id, 128) || null,
    rulesJson,
    text(body.indicator_name, 160) || null,
    text(body.indicator_version, 96) || null,
    configJson,
    text(body.change_note, 1600) || null,
    isCurrent ? 1 : 0,
  ));
  statements.push(env.DB.prepare("UPDATE strategy_profiles SET updated_at = ?2 WHERE id = ?1").bind(strategyId, now));
  await env.DB.batch(statements);
  return { id, strategy_id: strategyId, version_label: versionLabel, status, evidence_stage: evidenceStage, is_current: isCurrent };
}

async function createObservation(env, body) {
  const versionId = text(body.strategy_version_id, 128);
  if (!versionId || !(await versionExists(env, versionId))) throw new Error("strategy_version_not_found");
  const observationType = text(body.observation_type, 64).toUpperCase();
  if (!observationType) throw new Error("observation_type_required");
  const id = text(body.id || crypto.randomUUID(), 128);
  const now = new Date().toISOString();
  const sessionEventId = text(body.session_event_id, 128) || null;
  const signalEventId = text(body.signal_event_id, 128) || null;
  const journalEntryId = text(body.journal_entry_id, 128) || null;
  const note = text(body.note, 2000) || null;
  if (!sessionEventId && !signalEventId && !journalEntryId && !note) throw new Error("observation_link_or_note_required");

  await env.DB.prepare(
    `INSERT INTO strategy_observations (
       id, created_at, strategy_version_id, observation_type,
       session_event_id, signal_event_id, journal_entry_id,
       outcome, note, metadata_json
     ) VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7, ?8, ?9, ?10)`,
  ).bind(
    id,
    now,
    versionId,
    observationType,
    sessionEventId,
    signalEventId,
    journalEntryId,
    text(body.outcome, 160) || null,
    note,
    jsonString(body.metadata, {}),
  ).run();
  return { id, strategy_version_id: versionId, observation_type: observationType };
}

export async function handleStrategyDnaRequest(request, env) {
  if (!env.DB) return json({ ok: false, error: "strategy_dna_storage_not_configured" }, 503);
  if (!authorized(request, env)) return json({ ok: false, error: "unauthorized" }, 401);
  const url = new URL(request.url);

  try {
    if (request.method === "GET" && url.pathname === "/strategy-dna") {
      const strategies = await listStrategies(env);
      return json({ ok: true, count: strategies.length, strategies });
    }

    const detailMatch = url.pathname.match(/^\/strategy-dna\/strategy\/([^/]+)$/);
    if (request.method === "GET" && detailMatch) {
      const detail = await strategyDetail(env, decodeURIComponent(detailMatch[1]));
      if (!detail) return json({ ok: false, error: "strategy_not_found" }, 404);
      return json({ ok: true, ...detail });
    }

    if (request.method === "POST" && url.pathname === "/strategy-dna/profile") {
      const result = await upsertProfile(env, await readJson(request));
      return json({ ok: true, profile: result }, 201);
    }

    if (request.method === "POST" && url.pathname === "/strategy-dna/version") {
      const result = await createVersion(env, await readJson(request));
      return json({ ok: true, version: result }, 201);
    }

    if (request.method === "POST" && url.pathname === "/strategy-dna/observation") {
      const result = await createObservation(env, await readJson(request));
      return json({ ok: true, observation: result }, 201);
    }

    return json({ ok: false, error: "not_found" }, 404);
  } catch (error) {
    const code = error instanceof SyntaxError ? "invalid_json" : String(error?.message || "strategy_dna_error");
    const status = code === "body_too_large" ? 413 : code.includes("not_found") ? 404 : 400;
    return json({ ok: false, error: code }, status);
  }
}
