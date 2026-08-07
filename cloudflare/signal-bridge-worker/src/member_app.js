const COOKIE_NAME = "sb_member";
const MEMBER_SESSION_HOURS = 24;
const LOGIN_MINUTES = 10;
const WORKER_BASE = "https://signal-bridge-webhook.airy-iris.workers.dev";

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

async function listOwnJournal(session, env, limit = 50) {
  const safeLimit = Math.min(Math.max(Number(limit) || 50, 1), 100);
  const result = await env.DB.prepare(
    `SELECT id, created_at, journal_time, symbol, side, setup, strategy, title,
            raw_text, summary, result, pnl, rr, tags, source, signal_event_id,
            image_url, visibility, review_status
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

function journalCard(entry, canManage) {
  const when = escapeHtml(entry.journal_time || entry.created_at || "");
  const identity = [entry.symbol, entry.side, entry.result].filter(Boolean).map(escapeHtml).join(" · ") || "Unclassified";
  const title = escapeHtml(entry.title || entry.setup || "Journal entry");
  const note = escapeHtml(entry.summary || entry.raw_text || "");
  const image = entry.image_url
    ? `<a class="media" href="${escapeHtml(entry.image_url)}" target="_blank" rel="noopener"><img src="${escapeHtml(entry.image_url)}" alt="Journal chart" loading="lazy"></a>`
    : "";
  const action = canManage
    ? `<button data-id="${escapeHtml(entry.id.slice(0, 8))}" data-action="${entry.visibility === "PUBLISHED" ? "private" : "publish"}">${entry.visibility === "PUBLISHED" ? "Make private" : "Publish"}</button>`
    : "";
  return `<article class="entry">
    <div class="entry-top"><div><span class="state ${entry.visibility === "PUBLISHED" ? "pub" : "priv"}">${escapeHtml(entry.visibility)}</span><span class="id">${escapeHtml(entry.id.slice(0, 8))}</span></div><time>${when}</time></div>
    ${image}
    <h3>${title}</h3>
    <div class="identity">${identity}</div>
    <p>${note}</p>
    <div class="entry-foot"><span>${escapeHtml(entry.review_status || "RAW")}</span>${action}</div>
  </article>`;
}

function renderJournalPage(entries, session) {
  const cards = entries.length
    ? entries.map((entry) => journalCard(entry, Boolean(session.can_manage_journal))).join("")
    : `<div class="empty"><strong>No journal records yet.</strong><span>Use /journal or Capture to Journal in Discord and they will appear here privately.</span></div>`;
  return `<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Signal Bridge · My Journal</title><style>
    :root{color-scheme:dark;--bg:#060a11;--card:#0d1622;--line:#1d3044;--text:#e7f0fa;--muted:#8398ad;--blue:#59b8ff;--green:#51d99b;--amber:#e6bd69}*{box-sizing:border-box}body{margin:0;background:radial-gradient(circle at 80% 0,#10243c 0,transparent 34%),var(--bg);color:var(--text);font-family:Inter,ui-sans-serif,system-ui,-apple-system,sans-serif}.shell{width:min(980px,calc(100% - 28px));margin:auto}.top{position:sticky;top:0;z-index:4;background:rgba(6,10,17,.9);backdrop-filter:blur(15px);border-bottom:1px solid var(--line)}.top .shell{min-height:64px;display:flex;align-items:center;justify-content:space-between;gap:15px}.brand{font-weight:950;letter-spacing:.08em}.brand span{color:var(--blue)}a{color:#9fd3ff}.logout{font-size:12px;color:var(--muted)}main{padding:48px 0 80px}.hero{display:flex;justify-content:space-between;align-items:end;gap:20px;margin-bottom:24px}.eyebrow{color:#72bdf6;text-transform:uppercase;letter-spacing:.12em;font-size:10px;font-weight:900}h1{margin:8px 0 7px;font-size:clamp(34px,8vw,62px);letter-spacing:-.055em}.hero p{margin:0;color:var(--muted);max-width:620px;line-height:1.6}.badge{border:1px solid rgba(81,217,155,.25);background:rgba(81,217,155,.06);color:#79e4b5;border-radius:999px;padding:7px 10px;font-size:10px;font-weight:850}.list{display:grid;gap:13px}.entry{border:1px solid var(--line);border-radius:18px;padding:17px;background:linear-gradient(160deg,rgba(14,25,39,.96),rgba(8,14,23,.98));box-shadow:0 20px 55px rgba(0,0,0,.18)}.entry-top,.entry-foot{display:flex;justify-content:space-between;align-items:center;gap:10px}.entry-top time{color:#607991;font-size:9px}.state{display:inline-flex;border-radius:999px;padding:4px 7px;font-size:8px;font-weight:900;letter-spacing:.08em}.state.priv{color:#e9c87d;border:1px solid rgba(230,189,105,.25);background:rgba(230,189,105,.06)}.state.pub{color:#7be4b4;border:1px solid rgba(81,217,155,.25);background:rgba(81,217,155,.06)}.id{margin-left:8px;color:#68829b;font-size:9px}.media{display:block;margin:14px 0;border:1px solid var(--line);border-radius:13px;overflow:hidden;background:#05090e}.media img{display:block;width:100%;max-height:540px;object-fit:contain}.entry h3{margin:16px 0 4px;font-size:18px}.identity{color:#8fc8f7;font-size:10px;font-weight:850;text-transform:uppercase;letter-spacing:.07em}.entry p{white-space:pre-wrap;color:#a6b7c8;line-height:1.62;font-size:13px}.entry-foot{border-top:1px solid var(--line);padding-top:12px;color:#667f96;font-size:9px}.entry-foot button{border:1px solid rgba(89,184,255,.28);background:rgba(89,184,255,.08);color:#a8d8ff;border-radius:9px;padding:8px 10px;font:inherit;font-weight:850;cursor:pointer}.empty{border:1px dashed var(--line);border-radius:18px;padding:45px;text-align:center;color:var(--muted)}.empty strong,.empty span{display:block}.empty strong{color:var(--text);margin-bottom:7px}.notice{margin:14px 0;color:#82a0ba;font-size:11px}@media(max-width:640px){main{padding-top:30px}.hero{display:block}.badge{display:inline-block;margin-top:14px}.entry{padding:14px}.shell{width:min(100% - 20px,980px)}}
  </style></head><body><header class="top"><div class="shell"><div class="brand">SIGNAL <span>BRIDGE</span></div><a class="logout" href="/member/logout">Log out</a></div></header><main class="shell"><section class="hero"><div><span class="eyebrow">Private member workspace</span><h1>My Journal</h1><p>Your Discord journal records live here whether they are private or published. Raw notes stay tied to the source record; review and publishing happen around them.</p></div><span class="badge">Discord linked</span></section><div id="notice" class="notice"></div><section class="list">${cards}</section></main><script>
    document.addEventListener('click',async(e)=>{const b=e.target.closest('button[data-action]');if(!b)return;b.disabled=true;const n=document.getElementById('notice');n.textContent='Updating journal…';try{const r=await fetch('/member/api/journal/'+encodeURIComponent(b.dataset.id)+'/'+b.dataset.action,{method:'POST',headers:{'content-type':'application/json'}});const j=await r.json();if(!r.ok||!j.ok)throw new Error(j.error||'update_failed');location.reload()}catch(err){n.textContent='Could not update journal: '+err.message;b.disabled=false}});
  </script></body></html>`;
}

export async function handleMemberRequest(request, env) {
  if (!env.DB) return html("Signal Bridge member storage is not ready.", 503);
  const url = new URL(request.url);

  if (url.pathname === "/member/login") {
    const consumed = await consumeLoginToken(url.searchParams.get("token") || "", env);
    if (!consumed) return html("<h1>Signal Bridge</h1><p>This sign-in link is invalid, expired, or already used. Generate a new link from Discord.</p>", 401);
    return new Response(null, {
      status: 302,
      headers: { location: "/member/journal", "set-cookie": sessionCookie(consumed.sessionToken), "cache-control": "no-store" },
    });
  }

  if (url.pathname === "/member/logout") {
    return new Response(null, { status: 302, headers: { location: "/", "set-cookie": clearSessionCookie(), "cache-control": "no-store" } });
  }

  const session = await loadSession(request, env);
  if (!session) {
    if (url.pathname.startsWith("/member/api/")) return json({ ok: false, error: "not_authenticated" }, 401);
    return html("<h1>Signal Bridge</h1><p>Your private member session is missing or expired. Use <strong>/journal-login</strong> in Discord for a fresh one-time sign-in link.</p>", 401);
  }

  if (request.method === "GET" && url.pathname === "/member/journal") {
    const entries = await listOwnJournal(session, env, 100);
    return html(renderJournalPage(entries, session));
  }

  if (request.method === "GET" && url.pathname === "/member/api/journal") {
    const entries = await listOwnJournal(session, env, url.searchParams.get("limit") || 50);
    return json({ ok: true, count: entries.length, entries });
  }

  const match = url.pathname.match(/^\/member\/api\/journal\/([^/]+)\/(publish|private)$/);
  if (request.method === "POST" && match) {
    const desired = match[2] === "publish" ? "PUBLISHED" : "PRIVATE";
    const result = await setOwnVisibility(match[1], desired, session, env);
    if (result.error) return json({ ok: false, error: result.error }, result.error === "not_allowed" ? 403 : 400);
    return json({ ok: true, ...result });
  }

  return json({ ok: false, error: "not_found" }, 404);
}
