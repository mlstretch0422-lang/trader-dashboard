const ALLOWED_RESULTS = new Set(["WIN", "LOSS", "BE", "OPEN", "PASS", "NA"]);
const ALLOWED_SIDES = new Set(["LONG", "SHORT", "WAIT"]);
const ALLOWED_VISIBILITY = new Set(["PRIVATE", "PUBLISHED"]);
const ALLOWED_REVIEW_STATUS = new Set(["RAW", "NORMALIZED", "REVIEWED"]);
const MAX_LIMIT = 100;
const SITE_ORIGIN = "https://mlstretch0422-lang.github.io";
const JOURNAL_URL = "https://mlstretch0422-lang.github.io/trader-dashboard/journal.html";

function json(body, status = 200, extraHeaders = {}) {
  return new Response(JSON.stringify(body), {
    status,
    headers: {
      "content-type": "application/json; charset=utf-8",
      "cache-control": "no-store",
      "access-control-allow-origin": SITE_ORIGIN,
      "access-control-allow-headers": "authorization, content-type",
      "access-control-allow-methods": "GET, PATCH, POST, OPTIONS",
      ...extraHeaders,
    },
  });
}

function tokenFrom(request) {
  const auth = request.headers.get("authorization") || "";
  return auth.startsWith("Bearer ") ? auth.slice(7) : "";
}

function adminToken(env) {
  return env.JOURNAL_ADMIN_TOKEN || env.JOURNAL_INGEST_TOKEN || "";
}

function authorized(request, env) {
  const expected = adminToken(env);
  return Boolean(expected) && tokenFrom(request) === expected;
}

function safeText(value, maxLength) {
  return String(value ?? "").trim().slice(0, maxLength);
}

function parseTags(value) {
  if (value === undefined) return undefined;
  let tags = value;
  if (typeof tags === "string") tags = tags.split(",").map((tag) => tag.trim()).filter(Boolean);
  if (!Array.isArray(tags)) throw new Error("invalid_tags");
  return JSON.stringify(tags.slice(0, 20).map((tag) => safeText(tag, 40)).filter(Boolean));
}

function parseNullableNumber(value) {
  if (value === undefined) return undefined;
  if (value === null || value === "") return null;
  const number = Number(value);
  if (!Number.isFinite(number)) throw new Error("invalid_number");
  return number;
}

function parseEntry(entry) {
  if (!entry) return null;
  let tags = [];
  try { tags = JSON.parse(entry.tags || "[]"); } catch { tags = []; }
  return { ...entry, tags, public_url: entry.visibility === "PUBLISHED" ? JOURNAL_URL : null };
}

async function resolveEntryByIdOrPrefix(idValue, env) {
  const id = safeText(idValue, 64);
  if (id.length < 6) return { error: "journal_id_too_short" };

  const exact = await env.DB.prepare(
    `SELECT * FROM journal_entries WHERE id = ?1 LIMIT 1`,
  ).bind(id).run();
  const exactEntry = Array.isArray(exact.results) ? exact.results[0] : null;
  if (exactEntry) return { entry: exactEntry };

  const prefix = await env.DB.prepare(
    `SELECT * FROM journal_entries WHERE id LIKE ?1 ORDER BY created_at DESC LIMIT 2`,
  ).bind(`${id}%`).run();
  const matches = Array.isArray(prefix.results) ? prefix.results : [];
  if (!matches.length) return { error: "journal_not_found" };
  if (matches.length > 1) return { error: "journal_id_ambiguous" };
  return { entry: matches[0] };
}

async function listEntries(url, env) {
  const rawLimit = Number.parseInt(url.searchParams.get("limit") || "50", 10);
  const limit = Number.isFinite(rawLimit) ? Math.min(Math.max(rawLimit, 1), MAX_LIMIT) : 50;
  const visibility = safeText(url.searchParams.get("visibility"), 16).toUpperCase();
  const reviewStatus = safeText(url.searchParams.get("review_status"), 16).toUpperCase();
  const author = safeText(url.searchParams.get("author"), 32);
  const symbol = safeText(url.searchParams.get("symbol"), 32).toUpperCase();

  if (visibility && !ALLOWED_VISIBILITY.has(visibility)) return json({ ok: false, error: "invalid_visibility" }, 400);
  if (reviewStatus && !ALLOWED_REVIEW_STATUS.has(reviewStatus)) return json({ ok: false, error: "invalid_review_status" }, 400);

  const where = [];
  const values = [];
  const add = (column, value) => {
    where.push(`${column} = ?${values.length + 1}`);
    values.push(value);
  };
  if (visibility) add("visibility", visibility);
  if (reviewStatus) add("review_status", reviewStatus);
  if (author) add("discord_author_id", author);
  if (symbol) add("symbol", symbol);

  values.push(limit);
  const whereClause = where.length ? `WHERE ${where.join(" AND ")}` : "";
  const result = await env.DB.prepare(
    `SELECT * FROM journal_entries ${whereClause}
     ORDER BY COALESCE(journal_time, created_at) DESC
     LIMIT ?${values.length}`,
  ).bind(...values).run();
  const entries = (Array.isArray(result.results) ? result.results : []).map(parseEntry);
  return json({ ok: true, count: entries.length, entries });
}

async function setVisibility(entry, visibility, env) {
  const reviewStatus = visibility === "PUBLISHED" ? "REVIEWED" : entry.review_status;
  await env.DB.prepare(
    `UPDATE journal_entries
     SET visibility = ?2, review_status = ?3
     WHERE id = ?1`,
  ).bind(entry.id, visibility, reviewStatus).run();
  const refreshed = await env.DB.prepare(`SELECT * FROM journal_entries WHERE id = ?1 LIMIT 1`).bind(entry.id).run();
  return parseEntry(Array.isArray(refreshed.results) ? refreshed.results[0] : null);
}

async function patchEntry(entry, request, env) {
  const raw = await request.json();
  const updates = [];
  const values = [];
  const set = (column, value) => {
    updates.push(`${column} = ?${values.length + 1}`);
    values.push(value);
  };

  if (raw.symbol !== undefined) set("symbol", safeText(raw.symbol, 32).toUpperCase() || null);
  if (raw.side !== undefined) {
    const value = safeText(raw.side, 16).toUpperCase();
    if (value && !ALLOWED_SIDES.has(value)) throw new Error("invalid_side");
    set("side", value || null);
  }
  if (raw.setup !== undefined) set("setup", safeText(raw.setup, 96) || null);
  if (raw.strategy !== undefined) set("strategy", safeText(raw.strategy, 96) || null);
  if (raw.title !== undefined) set("title", safeText(raw.title, 160) || null);
  if (raw.summary !== undefined) set("summary", safeText(raw.summary, 600) || null);
  if (raw.result !== undefined) {
    const value = safeText(raw.result, 16).toUpperCase();
    if (!ALLOWED_RESULTS.has(value)) throw new Error("invalid_result");
    set("result", value);
  }
  const pnl = parseNullableNumber(raw.pnl);
  if (pnl !== undefined) set("pnl", pnl);
  const rr = parseNullableNumber(raw.rr);
  if (rr !== undefined) set("rr", rr);
  const tags = parseTags(raw.tags);
  if (tags !== undefined) set("tags", tags);
  if (raw.signal_event_id !== undefined) set("signal_event_id", safeText(raw.signal_event_id, 64) || null);
  if (raw.image_url !== undefined) set("image_url", safeText(raw.image_url, 1024) || null);
  if (raw.review_status !== undefined) {
    const value = safeText(raw.review_status, 16).toUpperCase();
    if (!ALLOWED_REVIEW_STATUS.has(value)) throw new Error("invalid_review_status");
    set("review_status", value);
  }
  if (raw.visibility !== undefined) {
    const value = safeText(raw.visibility, 16).toUpperCase();
    if (!ALLOWED_VISIBILITY.has(value)) throw new Error("invalid_visibility");
    set("visibility", value);
    if (value === "PUBLISHED" && raw.review_status === undefined) set("review_status", "REVIEWED");
  }

  // raw_text and provenance fields are intentionally immutable here.
  if (!updates.length) return parseEntry(entry);
  values.push(entry.id);
  await env.DB.prepare(
    `UPDATE journal_entries SET ${updates.join(", ")} WHERE id = ?${values.length}`,
  ).bind(...values).run();
  const refreshed = await env.DB.prepare(`SELECT * FROM journal_entries WHERE id = ?1 LIMIT 1`).bind(entry.id).run();
  return parseEntry(Array.isArray(refreshed.results) ? refreshed.results[0] : null);
}

export async function handleJournalAdminRequest(request, env) {
  if (request.method === "OPTIONS") return json({ ok: true });
  if (!env.DB) return json({ ok: false, error: "journal_storage_not_configured" }, 503);
  if (!adminToken(env)) return json({ ok: false, error: "journal_admin_not_configured" }, 503);
  if (!authorized(request, env)) return json({ ok: false, error: "unauthorized" }, 401);

  const url = new URL(request.url);
  const parts = url.pathname.split("/").filter(Boolean);

  try {
    if (parts.length === 1 && request.method === "GET") return await listEntries(url, env);
    if (parts.length < 2) return json({ ok: false, error: "not_found" }, 404);

    const resolved = await resolveEntryByIdOrPrefix(parts[1], env);
    if (resolved.error) return json({ ok: false, error: resolved.error }, resolved.error === "journal_not_found" ? 404 : 400);
    const entry = resolved.entry;

    if (parts.length === 2 && request.method === "GET") return json({ ok: true, entry: parseEntry(entry) });
    if (parts.length === 2 && request.method === "PATCH") {
      const updated = await patchEntry(entry, request, env);
      return json({ ok: true, entry: updated });
    }
    if (parts.length === 3 && request.method === "POST" && parts[2] === "publish") {
      const updated = await setVisibility(entry, "PUBLISHED", env);
      return json({ ok: true, entry: updated });
    }
    if (parts.length === 3 && request.method === "POST" && parts[2] === "private") {
      const updated = await setVisibility(entry, "PRIVATE", env);
      return json({ ok: true, entry: updated });
    }
    return json({ ok: false, error: "not_found" }, 404);
  } catch (error) {
    const reason = error instanceof SyntaxError ? "invalid_json" : String(error?.message || "journal_admin_failed");
    return json({ ok: false, error: reason }, 400);
  }
}
