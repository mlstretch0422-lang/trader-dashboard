const COOKIE_NAME = "sb_member";
const MEMBER_SESSION_HOURS = 24;
const LOGIN_MINUTES = 10;
const WORKER_BASE = "https://signal-bridge-webhook.airy-iris.workers.dev";
const PUBLIC_BASE = "https://mlstretch0422-lang.github.io/trader-dashboard";
const EVIDENCE_STAGES = new Set([
  "PROJECT_RULE",
  "IMPLEMENTED",
  "BACKTESTED",
  "ISOLATED_ATTRIBUTION",
  "WALK_FORWARD",
  "PAPER_FORWARD",
  "LIVE",
]);

function text(value, maxLength = 4000) {
  return String(value ?? "").trim().slice(0, maxLength);
}

function json(body, status = 200, headers = {}) {
  return new Response(JSON.stringify(body), {
    status,
    headers: {
      "content-type": "application/json; charset=utf-8",
      "cache-control": "no-store",
      ...headers,
    },
  });
}

function html(body, status = 200, headers = {}) {
  return new Response(body, {
    status,
    headers: {
      "content-type": "text/html; charset=utf-8",
      "cache-control": "no-store, private",
      "x-frame-options": "DENY",
      "content-security-policy": "default-src 'none'; img-src https: data:; style-src 'unsafe-inline'; script-src 'unsafe-inline'; connect-src 'self'; base-uri 'none'; form-action 'self'",
      "referrer-policy": "no-referrer",
      ...headers,
    },
  });
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function randomToken(bytes = 32) {
  const data = new Uint8Array(bytes);
  crypto.getRandomValues(data);
  let binary = "";
  for (const byte of data) binary += String.fromCharCode(byte);
  return btoa(binary).replaceAll("+", "-").replaceAll("/", "_").replaceAll("=", "");
}

async function sha256(value) {
  const digest = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(value));
  return [...new Uint8Array(digest)].map((b) => b.toString(16).padStart(2, "0")).join("");
}

function isoAfterMinutes(minutes) {
  return new Date(Date.now() + minutes * 60_000).toISOString();
}

function isoAfterHours(hours) {
  return new Date(Date.now() + hours * 3_600_000).toISOString();
}

function cookieValue(request) {
  const cookie = request.headers.get("cookie") || "";
  for (const pair of cookie.split(";")) {
    const [name, ...rest] = pair.trim().split("=");
    if (name === COOKIE_NAME) return rest.join("=");
  }
  return "";
}

function sessionCookie(token) {
  return `${COOKIE_NAME}=${token}; Path=/member; Max-Age=${MEMBER_SESSION_HOURS * 3600}; HttpOnly; Secure; SameSite=Lax`;
}

function clearSessionCookie() {
  return `${COOKIE_NAME}=; Path=/member; Max-Age=0; HttpOnly; Secure; SameSite=Lax`;
}

export async function createMemberLoginLink({ userId, guildId, canManageJournal }, env) {
  if (!env.DB) throw new Error("member_storage_not_configured");
  if (!userId) throw new Error("discord_user_missing");

  const rawToken = randomToken(32);
  const tokenHash = await sha256(rawToken);
  const now = new Date().toISOString();
  await env.DB.prepare(
    `INSERT INTO member_login_tokens (
      token_hash, created_at, expires_at, discord_user_id, discord_guild_id,
      can_manage_journal, used_at
    ) VALUES (?1, ?2, ?3, ?4, ?5, ?6, NULL)`,
  ).bind(
    tokenHash,
    now,
    isoAfterMinutes(LOGIN_MINUTES),
    userId,
    guildId || null,
    canManageJournal ? 1 : 0,
  ).run();

  return `${WORKER_BASE}/member/login?token=${encodeURIComponent(rawToken)}`;
}

async function consumeLoginToken(rawToken, env) {
  if (!env.DB || !rawToken) return null;
  const tokenHash = await sha256(rawToken);
  const result = await env.DB.prepare(
    `SELECT * FROM member_login_tokens
     WHERE token_hash = ?1 AND used_at IS NULL AND expires_at > ?2
     LIMIT 1`,
  ).bind(tokenHash, new Date().toISOString()).run();
  const login = Array.isArray(result.results) ? result.results[0] || null : null;
  if (!login) return null;

  const sessionToken = randomToken(32);
  const sessionHash = await sha256(sessionToken);
  const now = new Date().toISOString();
  await env.DB.batch([
    env.DB.prepare(`UPDATE member_login_tokens SET used_at = ?2 WHERE token_hash = ?1`).bind(tokenHash, now),
    env.DB.prepare(
      `INSERT INTO member_sessions (
        session_hash, created_at, expires_at, discord_user_id, discord_guild_id,
        can_manage_journal, revoked_at
      ) VALUES (?1, ?2, ?3, ?4, ?5, ?6, NULL)`,
    ).bind(
      sessionHash,
      now,
      isoAfterHours(MEMBER_SESSION_HOURS),
      login.discord_user_id,
      login.discord_guild_id,
      login.can_manage_journal || 0,
    ),
  ]);
  return { sessionToken, login };
}

async function loadSession(request, env) {
  if (!env.DB) return null;
  const raw = cookieValue(request);
  if (!raw) return null;
  const hash = await sha256(raw);
  const result = await env.DB.prepare(
    `SELECT * FROM member_sessions
     WHERE session_hash = ?1 AND revoked_at IS NULL AND expires_at > ?2
     LIMIT 1`,
  ).bind(hash, new Date().toISOString()).run();
  return Array.isArray(result.results) ? result.results[0] || null : null;
}

async function loadEntitlement(session, env) {
  if (!session || !env.DB) return null;
  const result = await env.DB.prepare(
    `SELECT * FROM member_entitlements
     WHERE discord_user_id = ?1
       AND status = 'ACTIVE'
       AND (expires_at IS NULL OR expires_at > ?2)
     LIMIT 1`,
  ).bind(session.discord_user_id, new Date().toISOString()).run();
  const row = Array.isArray(result.results) ? result.results[0] || null : null;
  if (row) return row;
  if (session.can_manage_journal) {
    return { discord_user_id: session.discord_user_id, tier: "ADMIN", status: "ACTIVE", source: "SESSION_MANAGER" };
  }
  return null;
}

async function requireMember(request, env) {
  const session = await loadSession(request, env);
  if (!session) return { error: "not_authenticated" };
  const entitlement = await loadEntitlement(session, env);
  if (!entitlement) return { error: "premium_access_required", session };
  return { session, entitlement };
}

async function listOwnJournal(session, env, limit = 50) {
  const safeLimit = Math.min(Math.max(Number(limit) || 50, 1), 100);
  const result = await env.DB.prepare(
    `SELECT id, created_at, journal_time, symbol, side, setup, strategy,
            strategy_version_id, title, raw_text, summary, result, pnl, rr,
            tags, source, signal_event_id, image_url, visibility, review_status
     FROM journal_entries
     WHERE discord_author_id = ?1
     ORDER BY COALESCE(journal_time, created_at) DESC
     LIMIT ?2`,
  ).bind(session.discord_user_id, safeLimit).run();
  return (Array.isArray(result.results) ? result.results : []).map((entry) => {
    let tags = [];
    try { tags = JSON.parse(entry.tags || "[]"); } catch { tags = []; }
    return { ...entry, tags };
  });
}

async function resolveOwnJournal(idPrefix, session, env) {
  const id = text(idPrefix, 64);
  if (id.length < 6) return { error: "journal_id_too_short" };
  const result = await env.DB.prepare(
    `SELECT * FROM journal_entries
     WHERE discord_author_id = ?1 AND id LIKE ?2
     ORDER BY created_at DESC LIMIT 2`,
  ).bind(session.discord_user_id, `${id}%`).run();
  const rows = Array.isArray(result.results) ? result.results : [];
  if (!rows.length) return { error: "journal_not_found" };
  if (rows.length > 1) return { error: "journal_id_ambiguous" };
  return { entry: rows[0] };
}

async function setOwnVisibility(idPrefix, visibility, session, env) {
  if (!session.can_manage_journal) return { error: "not_allowed" };
  const resolved = await resolveOwnJournal(idPrefix, session, env);
  if (resolved.error) return resolved;
  const reviewStatus = visibility === "PUBLISHED" ? "REVIEWED" : resolved.entry.review_status;
  await env.DB.prepare(
    `UPDATE journal_entries SET visibility = ?2, review_status = ?3 WHERE id = ?1`,
  ).bind(resolved.entry.id, visibility, reviewStatus).run();
  return { ok: true, id: resolved.entry.id, visibility };
}

async function listStrategies(session, env) {
  const result = await env.DB.prepare(
    `SELECT p.id, p.owner_type, p.owner_discord_id, p.slug, p.name, p.description, p.status,
            p.created_at, p.updated_at,
            v.id AS version_id, v.version_label, v.status AS version_status,
            v.evidence_stage, v.indicator_name, v.indicator_version, v.change_note,
            v.created_at AS version_created_at, v.is_current
     FROM strategy_profiles p
     LEFT JOIN strategy_versions v ON v.strategy_id = p.id
     WHERE p.owner_type = 'SYSTEM' OR p.owner_discord_id = ?1
     ORDER BY p.updated_at DESC, v.created_at DESC`,
  ).bind(session.discord_user_id).run();
  const rows = Array.isArray(result.results) ? result.results : [];
  const profiles = new Map();
  for (const row of rows) {
    if (!profiles.has(row.id)) {
      profiles.set(row.id, {
        id: row.id,
        owner_type: row.owner_type,
        owner_discord_id: row.owner_discord_id,
        slug: row.slug,
        name: row.name,
        description: row.description,
        status: row.status,
        created_at: row.created_at,
        updated_at: row.updated_at,
        versions: [],
      });
    }
    if (row.version_id) {
      profiles.get(row.id).versions.push({
        id: row.version_id,
        version_label: row.version_label,
        status: row.version_status,
        evidence_stage: row.evidence_stage,
        indicator_name: row.indicator_name,
        indicator_version: row.indicator_version,
        change_note: row.change_note,
        created_at: row.version_created_at,
        is_current: Boolean(row.is_current),
      });
    }
  }
  return [...profiles.values()];
}

function slugify(value) {
  return text(value, 96).toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "").slice(0, 64) || "strategy";
}

async function createMemberStrategy(session, env, body) {
  const name = text(body?.name, 120);
  if (!name) throw new Error("strategy_name_required");
  const description = text(body?.description, 1200) || null;
  const id = `member-${session.discord_user_id}-${crypto.randomUUID()}`;
  const now = new Date().toISOString();
  let slug = slugify(name);
  const duplicate = await env.DB.prepare(
    `SELECT COUNT(*) AS total FROM strategy_profiles
     WHERE owner_type = 'MEMBER' AND owner_discord_id = ?1 AND slug LIKE ?2`,
  ).bind(session.discord_user_id, `${slug}%`).run();
  const count = Number(duplicate.results?.[0]?.total || 0);
  if (count) slug = `${slug}-${count + 1}`.slice(0, 80);
  await env.DB.prepare(
    `INSERT INTO strategy_profiles (
       id, created_at, updated_at, owner_type, owner_discord_id, slug, name, description, status
     ) VALUES (?1, ?2, ?2, 'MEMBER', ?3, ?4, ?5, ?6, 'ACTIVE')`,
  ).bind(id, now, session.discord_user_id, slug, name, description).run();
  return { id, slug, name };
}

async function ownStrategy(strategyId, session, env) {
  const result = await env.DB.prepare(
    `SELECT * FROM strategy_profiles
     WHERE id = ?1 AND owner_type = 'MEMBER' AND owner_discord_id = ?2 LIMIT 1`,
  ).bind(strategyId, session.discord_user_id).run();
  return result.results?.[0] || null;
}

async function createMemberVersion(strategyId, session, env, body) {
  const profile = await ownStrategy(strategyId, session, env);
  if (!profile) throw new Error("strategy_not_owned");
  const versionLabel = text(body?.version_label, 96);
  if (!versionLabel) throw new Error("version_label_required");
  const evidenceStage = text(body?.evidence_stage || "PROJECT_RULE", 48).toUpperCase();
  if (!EVIDENCE_STAGES.has(evidenceStage)) throw new Error("invalid_evidence_stage");
  const id = crypto.randomUUID();
  const now = new Date().toISOString();
  await env.DB.batch([
    env.DB.prepare("UPDATE strategy_versions SET is_current = 0 WHERE strategy_id = ?1").bind(strategyId),
    env.DB.prepare(
      `INSERT INTO strategy_versions (
         id, strategy_id, version_label, created_at, status, evidence_stage,
         parent_version_id, rules_json, indicator_name, indicator_version,
         indicator_config_json, change_note, is_current
       ) VALUES (?1, ?2, ?3, ?4, 'STAGED', ?5, NULL, '{}', NULL, NULL, '{}', ?6, 1)`,
    ).bind(id, strategyId, versionLabel, now, evidenceStage, text(body?.change_note, 1600) || null),
    env.DB.prepare("UPDATE strategy_profiles SET updated_at = ?2 WHERE id = ?1").bind(strategyId, now),
  ]);
  return { id, strategy_id: strategyId, version_label: versionLabel, evidence_stage: evidenceStage };
}

function nav(active) {
  const items = [
    ["home", "/member", "Home"],
    ["journal", "/member/journal", "My Journal"],
    ["strategies", "/member/strategy-lab", "Strategy Lab"],
    ["morning", `${PUBLIC_BASE}/signals.html#morning-desk`, "Morning Desk"],
  ];
  return items.map(([id, href, label]) => `<a class="${active === id ? "active" : ""}" href="${href}">${label}</a>`).join("");
}

function shell({ title, subtitle, content, session, entitlement, active = "home", script = "" }) {
  const tier = escapeHtml(entitlement?.tier || "MEMBER");
  const user = escapeHtml(String(session.discord_user_id || "").slice(-6));
  return `<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="theme-color" content="#060a11"><title>Signal Bridge · ${escapeHtml(title)}</title><style>
  :root{color-scheme:dark;--bg:#05080d;--panel:#0d1622;--panel2:#101b2a;--line:#1d3044;--text:#e8f1fb;--muted:#8499ae;--blue:#61c3ff;--violet:#a287ff;--green:#5de1aa;--amber:#e5b95f}*{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;background:radial-gradient(circle at 8% -4%,rgba(52,139,230,.22),transparent 28rem),radial-gradient(circle at 95% 0,rgba(162,135,255,.12),transparent 24rem),linear-gradient(180deg,#05080d,#09101a 50%,#05080d);color:var(--text);font-family:Inter,ui-sans-serif,system-ui,-apple-system,sans-serif;min-height:100vh}a{color:inherit}.shell{width:min(1120px,calc(100% - 28px));margin:auto}.top{position:sticky;top:0;z-index:10;background:rgba(5,8,13,.88);backdrop-filter:blur(16px);border-bottom:1px solid var(--line)}.topbar{min-height:68px;display:flex;align-items:center;gap:18px}.brand{font-weight:950;letter-spacing:.09em;white-space:nowrap}.brand span{color:var(--blue)}nav{display:flex;gap:5px;overflow:auto;margin-left:auto}nav a{text-decoration:none;color:#8399af;font-size:11px;font-weight:800;padding:8px 9px;border-radius:9px;white-space:nowrap}nav a.active{color:#dff1ff;background:rgba(97,195,255,.09);border:1px solid rgba(97,195,255,.14)}.access{border:1px solid rgba(93,225,170,.22);background:rgba(93,225,170,.06);color:#7fe7ba;border-radius:999px;padding:6px 9px;font-size:9px;font-weight:900;white-space:nowrap}.logout{color:#6e8399;font-size:10px;text-decoration:none}.hero{padding:46px 0 22px}.eyebrow{color:#88caff;font-size:9px;font-weight:900;text-transform:uppercase;letter-spacing:.12em}.hero h1{font-size:clamp(38px,8vw,68px);letter-spacing:-.06em;margin:8px 0 8px;background:linear-gradient(105deg,#fff,#bfe1ff 45%,#b39aff 80%);-webkit-background-clip:text;background-clip:text;color:transparent}.hero p{margin:0;color:var(--muted);max-width:760px;line-height:1.65;font-size:13px}.grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px;padding-bottom:70px}.card{border:1px solid var(--line);border-radius:18px;padding:18px;background:linear-gradient(155deg,rgba(14,25,39,.94),rgba(7,13,22,.98));box-shadow:0 20px 60px rgba(0,0,0,.15)}a.card{text-decoration:none;transition:.16s ease}a.card:hover{transform:translateY(-2px);border-color:rgba(97,195,255,.36)}.card .tag{color:#7fbce9;text-transform:uppercase;letter-spacing:.09em;font-size:8px;font-weight:900}.card h3{margin:10px 0 7px;font-size:19px}.card p{margin:0;color:#8297ac;font-size:11px;line-height:1.6}.card b.link{display:block;margin-top:16px;color:#a9d9ff;font-size:10px}.stats{display:grid;grid-template-columns:repeat(3,1fr);gap:8px;margin:18px 0 0}.stat{border:1px solid rgba(255,255,255,.05);border-radius:11px;padding:10px;background:rgba(255,255,255,.015)}.stat span{display:block;color:#6e849a;font-size:8px;text-transform:uppercase;letter-spacing:.08em}.stat strong{display:block;margin-top:5px;font-size:12px}.list{display:grid;gap:12px;padding-bottom:70px}.entry,.strategy{border:1px solid var(--line);border-radius:18px;padding:17px;background:linear-gradient(160deg,rgba(14,25,39,.96),rgba(8,14,23,.98))}.entry-top,.entry-foot,.strategy-top{display:flex;justify-content:space-between;align-items:center;gap:10px}.entry-top time{color:#607991;font-size:9px}.state{display:inline-flex;border-radius:999px;padding:4px 7px;font-size:8px;font-weight:900;letter-spacing:.08em}.state.priv{color:#e9c87d;border:1px solid rgba(230,189,105,.25);background:rgba(230,189,105,.06)}.state.pub{color:#7be4b4;border:1px solid rgba(81,217,155,.25);background:rgba(81,217,155,.06)}.id{margin-left:8px;color:#68829b;font-size:9px}.media{display:block;margin:14px 0;border:1px solid var(--line);border-radius:13px;overflow:hidden;background:#05090e}.media img{display:block;width:100%;max-height:540px;object-fit:contain}.entry h3,.strategy h3{margin:16px 0 4px;font-size:18px}.identity{color:#8fc8f7;font-size:10px;font-weight:850;text-transform:uppercase;letter-spacing:.07em}.entry p,.strategy p{white-space:pre-wrap;color:#a6b7c8;line-height:1.62;font-size:13px}.entry-foot{border-top:1px solid var(--line);padding-top:12px;color:#667f96;font-size:9px}.entry-foot button,.action{border:1px solid rgba(89,184,255,.28);background:rgba(89,184,255,.08);color:#a8d8ff;border-radius:9px;padding:8px 10px;font:inherit;font-weight:850;cursor:pointer}.empty{border:1px dashed var(--line);border-radius:18px;padding:45px;text-align:center;color:var(--muted)}.empty strong,.empty span{display:block}.empty strong{color:var(--text);margin-bottom:7px}.notice{margin:14px 0;color:#82a0ba;font-size:11px}.versions{display:grid;gap:7px;margin-top:13px}.version{display:grid;grid-template-columns:1fr auto;gap:10px;border-top:1px solid rgba(255,255,255,.055);padding-top:9px}.version strong{font-size:11px}.version span{color:#768da4;font-size:9px}.form{display:grid;gap:9px;margin-top:14px;border-top:1px solid var(--line);padding-top:13px}.form input,.form textarea,.form select{width:100%;border:1px solid var(--line);border-radius:10px;background:#09111c;color:var(--text);padding:10px;font:inherit;font-size:11px}.form textarea{min-height:74px;resize:vertical}.form-row{display:grid;grid-template-columns:1fr 1fr;gap:8px}.form button{justify-self:start}.system-badge{color:#b79fff;border:1px solid rgba(162,135,255,.21);background:rgba(162,135,255,.06);border-radius:999px;padding:4px 7px;font-size:8px;font-weight:900}.member-badge{color:#74e5b1;border:1px solid rgba(93,225,170,.21);background:rgba(93,225,170,.05);border-radius:999px;padding:4px 7px;font-size:8px;font-weight:900}@media(max-width:760px){.topbar{flex-wrap:wrap;padding:9px 0}.brand{flex:1}.access{order:2}.logout{order:2}nav{order:3;width:100%;margin:0}.hero{padding-top:32px}.grid{grid-template-columns:1fr}.stats{grid-template-columns:1fr 1fr}.form-row{grid-template-columns:1fr}}@media(max-width:430px){.shell{width:min(100% - 20px,1120px)}.stats{grid-template-columns:1fr}.hero h1{font-size:42px}}
  </style></head><body><header class="top"><div class="shell topbar"><div class="brand">SIGNAL <span>BRIDGE</span></div><nav>${nav(active)}</nav><span class="access">${tier}</span><a class="logout" href="/member/logout">Log out</a></div></header><main class="shell"><section class="hero"><span class="eyebrow">Discord-linked member ${user}</span><h1>${escapeHtml(title)}</h1><p>${escapeHtml(subtitle)}</p></section>${content}</main>${script ? `<script>${script}</script>` : ""}</body></html>`;
}

function journalCard(entry, canManage) {
  const when = escapeHtml(entry.journal_time || entry.created_at || "");
  const identity = [entry.symbol, entry.side, entry.result].filter(Boolean).map(escapeHtml).join(" · ") || "Unclassified";
  const title = escapeHtml(entry.title || entry.setup || "Journal entry");
  const note = escapeHtml(entry.summary || entry.raw_text || "");
  const image = entry.image_url
    ? `<a class="media" href="${escapeHtml(entry.image_url)}" target="_blank" rel="noopener"><img src="${escapeHtml(entry.image_url)}" alt="Journal chart" loading="lazy"></a>`
    : "";
  const dna = entry.strategy_version_id ? `<span>DNA ${escapeHtml(entry.strategy_version_id)}</span>` : "";
  const action = canManage
    ? `<button data-id="${escapeHtml(entry.id.slice(0, 8))}" data-action="${entry.visibility === "PUBLISHED" ? "private" : "publish"}">${entry.visibility === "PUBLISHED" ? "Make private" : "Publish"}</button>`
    : "";
  return `<article class="entry"><div class="entry-top"><div><span class="state ${entry.visibility === "PUBLISHED" ? "pub" : "priv"}">${escapeHtml(entry.visibility)}</span><span class="id">${escapeHtml(entry.id.slice(0, 8))}</span></div><time>${when}</time></div>${image}<h3>${title}</h3><div class="identity">${identity}</div><p>${note}</p><div class="entry-foot"><span>${escapeHtml(entry.review_status || "RAW")}</span>${dna}${action}</div></article>`;
}

function renderHome(session, entitlement, journalCount, strategies) {
  const ownedStrategies = strategies.filter((item) => item.owner_type === "MEMBER").length;
  const currentDna = strategies.flatMap((item) => item.versions || []).find((version) => version.is_current);
  const content = `<div class="stats"><div class="stat"><span>Journal records</span><strong>${journalCount}</strong></div><div class="stat"><span>Your strategies</span><strong>${ownedStrategies}</strong></div><div class="stat"><span>Flagship DNA</span><strong>${escapeHtml(currentDna?.version_label || "Ready")}</strong></div></div><section class="grid" style="margin-top:12px"><a class="card" href="/member/journal"><span class="tag">Private workspace</span><h3>My Journal</h3><p>Your Discord notes, charts, trades, passes, results, and linked strategy versions — private unless explicitly published.</p><b class="link">Open journal →</b></a><a class="card" href="${PUBLIC_BASE}/signals.html#morning-desk"><span class="tag">Live desk</span><h3>Morning Desk</h3><p>Session lifecycle, ORB state, transparent setup readiness, market intelligence, Signal Story, and durable alerts.</p><b class="link">Open Morning Desk →</b></a><a class="card" href="/member/strategy-lab"><span class="tag">Strategy DNA</span><h3>Strategy Lab</h3><p>Create your own strategy identity and preserve versions so rules and evidence do not get mixed together as the system changes.</p><b class="link">Open Strategy Lab →</b></a><a class="card" href="${PUBLIC_BASE}/indicators.html#premium-workspace"><span class="tag">Chart tools</span><h3>Indicator Workspace</h3><p>Indicator modules, presets, alert architecture, and the chart-side tools that will attach to Strategy DNA versions.</p><b class="link">Open Indicator Workspace →</b></a></section>`;
  return shell({ title:"Premium Workspace", subtitle:"The locked operating layer around your own trading: session intelligence, private journal records, strategy versions, and chart tools connected to the same system.", content, session, entitlement, active:"home" });
}

function renderJournalPage(entries, session, entitlement) {
  const cards = entries.length
    ? entries.map((entry) => journalCard(entry, Boolean(session.can_manage_journal))).join("")
    : `<div class="empty"><strong>No journal records yet.</strong><span>Use /journal or Capture to Journal in Discord and they will appear here privately.</span></div>`;
  const content = `<div id="notice" class="notice"></div><section class="list">${cards}</section>`;
  const script = `document.addEventListener('click',async(e)=>{const b=e.target.closest('button[data-action]');if(!b)return;b.disabled=true;const n=document.getElementById('notice');n.textContent='Updating journal…';try{const r=await fetch('/member/api/journal/'+encodeURIComponent(b.dataset.id)+'/'+b.dataset.action,{method:'POST',headers:{'content-type':'application/json'}});const j=await r.json();if(!r.ok||!j.ok)throw new Error(j.error||'update_failed');location.reload()}catch(err){n.textContent='Could not update journal: '+err.message;b.disabled=false}});`;
  return shell({ title:"My Journal", subtitle:"Your Discord journal records live here whether they are private or published. Raw notes stay tied to the source record while review and Strategy DNA build around them.", content, session, entitlement, active:"journal", script });
}

function strategyCard(strategy) {
  const owned = strategy.owner_type === "MEMBER";
  const versions = strategy.versions || [];
  const versionHtml = versions.length ? versions.map((version) => `<div class="version"><div><strong>${escapeHtml(version.version_label)}</strong><span>${escapeHtml(version.change_note || "Version snapshot")}</span></div><div><span>${escapeHtml(version.evidence_stage || "PROJECT_RULE")}${version.is_current ? " · CURRENT" : ""}</span></div></div>`).join("") : `<div class="version"><span>No versions yet.</span></div>`;
  const form = owned ? `<form class="form version-form" data-strategy="${escapeHtml(strategy.id)}"><div class="form-row"><input name="version_label" placeholder="Version label — e.g. v1.1" required><select name="evidence_stage"><option value="PROJECT_RULE">Project rule</option><option value="IMPLEMENTED">Implemented</option><option value="BACKTESTED">Backtested</option><option value="ISOLATED_ATTRIBUTION">Isolated attribution</option><option value="WALK_FORWARD">Walk-forward</option><option value="PAPER_FORWARD">Paper forward</option><option value="LIVE">Live</option></select></div><textarea name="change_note" placeholder="What changed in this version?"></textarea><button class="action" type="submit">Save version</button></form>` : "";
  return `<article class="strategy"><div class="strategy-top"><div><span class="${owned ? "member-badge" : "system-badge"}">${owned ? "YOUR STRATEGY" : "FLAGSHIP MODEL"}</span></div><span class="id">${escapeHtml(strategy.slug)}</span></div><h3>${escapeHtml(strategy.name)}</h3><p>${escapeHtml(strategy.description || "No description yet.")}</p><div class="versions">${versionHtml}</div>${form}</article>`;
}

function renderStrategyLab(strategies, session, entitlement) {
  const cards = strategies.map(strategyCard).join("") || `<div class="empty"><strong>No Strategy DNA yet.</strong><span>Create your first strategy below.</span></div>`;
  const content = `<section class="card" style="margin-bottom:12px"><span class="tag">Create Strategy DNA</span><h3>Start with the strategy identity.</h3><p>Give the idea a name and purpose. Versions get added underneath it as rules, indicators, tests, and forward evidence change.</p><form class="form" id="strategyForm"><input name="name" placeholder="Strategy name" required><textarea name="description" placeholder="What market/setup/process is this strategy trying to capture?"></textarea><button class="action" type="submit">Create strategy</button></form></section><div id="notice" class="notice"></div><section class="list">${cards}</section>`;
  const script = `const notice=document.getElementById('notice');async function post(url,body){const r=await fetch(url,{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify(body)});const j=await r.json();if(!r.ok||!j.ok)throw new Error(j.error||'request_failed');return j}document.getElementById('strategyForm')?.addEventListener('submit',async(e)=>{e.preventDefault();const f=new FormData(e.target);notice.textContent='Creating strategy…';try{await post('/member/api/strategies',{name:f.get('name'),description:f.get('description')});location.reload()}catch(err){notice.textContent='Could not create strategy: '+err.message}});document.querySelectorAll('.version-form').forEach(form=>form.addEventListener('submit',async(e)=>{e.preventDefault();const f=new FormData(form);notice.textContent='Saving version…';try{await post('/member/api/strategies/'+encodeURIComponent(form.dataset.strategy)+'/versions',{version_label:f.get('version_label'),evidence_stage:f.get('evidence_stage'),change_note:f.get('change_note')});location.reload()}catch(err){notice.textContent='Could not save version: '+err.message}}));`;
  return shell({ title:"Strategy Lab", subtitle:"Preserve the life of the strategy instead of overwriting it. Each version can eventually connect rules, indicator settings, sessions, signals, journal evidence, and what changed next.", content, session, entitlement, active:"strategies", script });
}

export async function handleMemberRequest(request, env) {
  if (!env.DB) return html("Signal Bridge member storage is not ready.", 503);
  const url = new URL(request.url);

  if (url.pathname === "/member/login") {
    const consumed = await consumeLoginToken(url.searchParams.get("token") || "", env);
    if (!consumed) return html("<h1>Signal Bridge</h1><p>This sign-in link is invalid, expired, or already used. Generate a new link from Discord.</p>", 401);
    return new Response(null, {
      status: 302,
      headers: { location: "/member", "set-cookie": sessionCookie(consumed.sessionToken), "cache-control": "no-store" },
    });
  }

  if (url.pathname === "/member/logout") {
    return new Response(null, { status: 302, headers: { location: PUBLIC_BASE, "set-cookie": clearSessionCookie(), "cache-control": "no-store" } });
  }

  const access = await requireMember(request, env);
  if (access.error) {
    if (url.pathname.startsWith("/member/api/")) return json({ ok:false, error:access.error }, 401);
    const detail = access.error === "premium_access_required"
      ? "Your Discord account is signed in, but it does not currently have active Signal Bridge access. Use /member-login in Discord after your role/access is updated."
      : "Use /member-login in the Signal Bridge Discord to generate a private one-time sign-in link.";
    return html(`<div style="font-family:system-ui;background:#05080d;color:#e8f1fb;min-height:100vh;padding:60px 24px"><div style="max-width:620px;margin:auto"><h1>Signal Bridge Premium</h1><p style="color:#8ca0b5;line-height:1.7">${detail}</p><a style="color:#79caff" href="${PUBLIC_BASE}">Return to preview site</a></div></div>`, 401);
  }
  const { session, entitlement } = access;

  if (request.method === "GET" && (url.pathname === "/member" || url.pathname === "/member/")) {
    const [entries, strategies] = await Promise.all([listOwnJournal(session, env, 100), listStrategies(session, env)]);
    return html(renderHome(session, entitlement, entries.length, strategies));
  }

  if (request.method === "GET" && url.pathname === "/member/journal") {
    const entries = await listOwnJournal(session, env, 100);
    return html(renderJournalPage(entries, session, entitlement));
  }

  if (request.method === "GET" && url.pathname === "/member/strategy-lab") {
    const strategies = await listStrategies(session, env);
    return html(renderStrategyLab(strategies, session, entitlement));
  }

  if (request.method === "GET" && url.pathname === "/member/api/journal") {
    const entries = await listOwnJournal(session, env, url.searchParams.get("limit") || 50);
    return json({ ok:true, count:entries.length, entries });
  }

  if (request.method === "GET" && url.pathname === "/member/api/strategies") {
    const strategies = await listStrategies(session, env);
    return json({ ok:true, count:strategies.length, strategies });
  }

  if (request.method === "POST" && url.pathname === "/member/api/strategies") {
    try {
      const body = await request.json();
      return json({ ok:true, strategy:await createMemberStrategy(session, env, body) }, 201);
    } catch (error) {
      return json({ ok:false, error:String(error?.message || "strategy_create_failed") }, 400);
    }
  }

  const versionMatch = url.pathname.match(/^\/member\/api\/strategies\/([^/]+)\/versions$/);
  if (request.method === "POST" && versionMatch) {
    try {
      const body = await request.json();
      const version = await createMemberVersion(decodeURIComponent(versionMatch[1]), session, env, body);
      return json({ ok:true, version }, 201);
    } catch (error) {
      const code = String(error?.message || "version_create_failed");
      return json({ ok:false, error:code }, code === "strategy_not_owned" ? 403 : 400);
    }
  }

  const journalMatch = url.pathname.match(/^\/member\/api\/journal\/([^/]+)\/(publish|private)$/);
  if (request.method === "POST" && journalMatch) {
    const desired = journalMatch[2] === "publish" ? "PUBLISHED" : "PRIVATE";
    const result = await setOwnVisibility(journalMatch[1], desired, session, env);
    if (result.error) return json({ ok:false, error:result.error }, result.error === "not_allowed" ? 403 : 400);
    return json({ ok:true, ...result });
  }

  return json({ ok:false, error:"not_found" }, 404);
}
