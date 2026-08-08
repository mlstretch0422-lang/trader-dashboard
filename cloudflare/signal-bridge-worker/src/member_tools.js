import { getMarketIntelligenceSummary } from "./market_intelligence.js";
import { getSessionSummaryData } from "./session_events.js";

const COOKIE_NAME = "sb_member";
const PUBLIC_BASE = "https://mlstretch0422-lang.github.io/trader-dashboard";

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function json(body, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "content-type": "application/json; charset=utf-8", "cache-control": "no-store, private" },
  });
}

function html(body, status = 200) {
  return new Response(body, {
    status,
    headers: {
      "content-type": "text/html; charset=utf-8",
      "cache-control": "no-store, private",
      "x-frame-options": "DENY",
      "referrer-policy": "no-referrer",
      "content-security-policy": "default-src 'none'; style-src 'unsafe-inline'; script-src 'unsafe-inline'; img-src https: data:; connect-src 'self'; base-uri 'none'; form-action 'self'",
    },
  });
}

function cookieValue(request) {
  const cookie = request.headers.get("cookie") || "";
  for (const pair of cookie.split(";")) {
    const [name, ...rest] = pair.trim().split("=");
    if (name === COOKIE_NAME) return rest.join("=");
  }
  return "";
}

async function sha256(value) {
  const digest = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(value));
  return [...new Uint8Array(digest)].map((byte) => byte.toString(16).padStart(2, "0")).join("");
}

async function memberAccess(request, env) {
  if (!env.DB) return { error: "member_storage_not_configured" };
  const raw = cookieValue(request);
  if (!raw) return { error: "not_authenticated" };
  const hash = await sha256(raw);
  const now = new Date().toISOString();
  const sessionResult = await env.DB.prepare(
    `SELECT * FROM member_sessions
     WHERE session_hash = ?1 AND revoked_at IS NULL AND expires_at > ?2
     LIMIT 1`,
  ).bind(hash, now).run();
  const session = sessionResult.results?.[0] || null;
  if (!session) return { error: "not_authenticated" };

  const entitlementResult = await env.DB.prepare(
    `SELECT * FROM member_entitlements
     WHERE discord_user_id = ?1
       AND status = 'ACTIVE'
       AND (expires_at IS NULL OR expires_at > ?2)
     LIMIT 1`,
  ).bind(session.discord_user_id, now).run();
  let entitlement = entitlementResult.results?.[0] || null;
  if (!entitlement && session.can_manage_journal) {
    entitlement = { tier: "ADMIN", status: "ACTIVE", source: "SESSION_MANAGER" };
  }
  if (!entitlement) return { error: "premium_access_required" };
  return { session, entitlement };
}

function nav(active) {
  const items = [
    ["home", "/member", "Home"],
    ["live", "/member/live", "Live Desk"],
    ["journal", "/member/journal", "My Journal"],
    ["strategies", "/member/strategy-lab", "Strategy Lab"],
    ["indicators", "/member/indicators", "Indicators"],
  ];
  return items.map(([id, href, label]) => `<a class="${active === id ? "active" : ""}" href="${href}">${label}</a>`).join("");
}

function shell({ active, title, subtitle, session, entitlement, content, script = "" }) {
  const tier = escapeHtml(entitlement?.tier || "MEMBER");
  const suffix = escapeHtml(String(session.discord_user_id || "").slice(-6));
  return `<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="theme-color" content="#05080d"><title>Signal Bridge · ${escapeHtml(title)}</title><style>
:root{color-scheme:dark;--bg:#05080d;--panel:#0d1622;--panel2:#101b2a;--line:#1e3146;--text:#eaf4ff;--muted:#8499ae;--blue:#61c3ff;--green:#5de1aa;--violet:#a287ff;--amber:#e7b85b;--red:#fb7185}*{box-sizing:border-box}body{margin:0;min-height:100vh;background:radial-gradient(circle at 10% 0,rgba(52,139,230,.20),transparent 28rem),radial-gradient(circle at 92% 0,rgba(162,135,255,.12),transparent 24rem),linear-gradient(180deg,#05080d,#09101a 52%,#05080d);color:var(--text);font-family:Inter,ui-sans-serif,system-ui,-apple-system,sans-serif}.shell{width:min(1180px,calc(100% - 28px));margin:auto}.top{position:sticky;top:0;z-index:20;border-bottom:1px solid var(--line);background:rgba(5,8,13,.9);backdrop-filter:blur(16px)}.bar{min-height:68px;display:flex;align-items:center;gap:16px}.brand{font-weight:950;letter-spacing:.09em;white-space:nowrap}.brand span{color:var(--blue)}nav{display:flex;gap:5px;margin-left:auto;overflow:auto}nav a{color:#8297ac;text-decoration:none;font-size:11px;font-weight:850;padding:8px 10px;border-radius:9px;white-space:nowrap}nav a.active{color:#dff2ff;background:rgba(97,195,255,.09);border:1px solid rgba(97,195,255,.14)}.tier{color:#78e4b3;border:1px solid rgba(93,225,170,.2);background:rgba(93,225,170,.06);padding:6px 9px;border-radius:999px;font-size:9px;font-weight:900}.logout{font-size:10px;color:#71879d;text-decoration:none}.hero{padding:42px 0 20px}.eyebrow{color:#88caff;font-size:9px;font-weight:900;text-transform:uppercase;letter-spacing:.12em}.hero h1{font-size:clamp(38px,8vw,68px);letter-spacing:-.055em;margin:8px 0;background:linear-gradient(110deg,#fff,#bfe3ff 46%,#b59fff 82%);-webkit-background-clip:text;background-clip:text;color:transparent}.hero p{max-width:800px;color:var(--muted);font-size:13px;line-height:1.7;margin:0}.grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px;padding-bottom:70px}.card{border:1px solid var(--line);border-radius:18px;padding:18px;background:linear-gradient(155deg,rgba(14,25,39,.95),rgba(7,13,22,.98));box-shadow:0 20px 60px rgba(0,0,0,.15)}a.card{text-decoration:none;transition:.16s ease}a.card:hover{transform:translateY(-2px);border-color:rgba(97,195,255,.36)}.tag{font-size:8px;font-weight:900;text-transform:uppercase;letter-spacing:.1em;color:#7fc6f7}.card h3{margin:9px 0 7px;font-size:20px}.card p{margin:0;color:#8ea3b8;font-size:12px;line-height:1.65}.link{display:block;margin-top:16px;color:#acdfff;font-size:10px;font-weight:900}.stats{display:grid;grid-template-columns:repeat(4,1fr);gap:8px;margin:17px 0 16px}.stat{border:1px solid rgba(255,255,255,.06);border-radius:12px;padding:11px;background:rgba(255,255,255,.018)}.stat span{display:block;color:#6f869d;font-size:8px;text-transform:uppercase;letter-spacing:.08em}.stat strong{display:block;margin-top:5px;font-size:13px}.section{padding:10px 0 70px}.section-head{display:flex;justify-content:space-between;gap:20px;align-items:end;margin-bottom:13px}.section-head h2{margin:6px 0 0;font-size:26px}.section-head p{max-width:560px;color:var(--muted);font-size:11px;line-height:1.6}.desk{display:grid;grid-template-columns:1.3fr .7fr;gap:12px}.levels{display:grid;grid-template-columns:repeat(4,1fr);gap:8px;margin-top:13px}.level,.mini{border:1px solid rgba(255,255,255,.06);border-radius:12px;padding:11px;background:rgba(255,255,255,.018)}.level span,.mini span{display:block;color:#71889e;font-size:8px;text-transform:uppercase;letter-spacing:.08em}.level strong,.mini strong{display:block;margin-top:5px;font-size:14px}.timeline{display:grid;gap:8px;margin-top:12px}.event{border-left:2px solid rgba(97,195,255,.4);padding:3px 0 3px 11px}.event b{display:block;font-size:11px}.event span{display:block;color:#7e94aa;font-size:9px;margin-top:3px}.headline{border-top:1px solid rgba(255,255,255,.06);padding:10px 0}.headline:first-child{border-top:0}.headline b{display:block;font-size:11px}.headline span{display:block;color:#748aa0;font-size:9px;margin-top:3px}.strategy{border:1px solid var(--line);border-radius:18px;padding:17px;background:linear-gradient(160deg,rgba(14,25,39,.96),rgba(8,14,23,.98));margin-bottom:12px}.strategy-top{display:flex;justify-content:space-between;gap:12px}.badge{font-size:8px;font-weight:900;border-radius:999px;padding:4px 7px}.member{color:#77e5b2;border:1px solid rgba(93,225,170,.22);background:rgba(93,225,170,.06)}.system{color:#b6a0ff;border:1px solid rgba(162,135,255,.22);background:rgba(162,135,255,.06)}.strategy h3{margin:13px 0 5px}.strategy p{margin:0;color:#879db2;font-size:11px;line-height:1.6}.version{margin-top:12px;padding-top:11px;border-top:1px solid rgba(255,255,255,.06)}.version-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:8px;margin-top:9px}.status{font-size:9px;font-weight:900;border-radius:999px;padding:5px 8px;display:inline-block}.ok{color:#74e7b1;background:rgba(93,225,170,.07);border:1px solid rgba(93,225,170,.2)}.warn{color:#f1cb78;background:rgba(231,184,91,.07);border:1px solid rgba(231,184,91,.22)}.bad{color:#ff93a2;background:rgba(251,113,133,.07);border:1px solid rgba(251,113,133,.22)}.form{display:grid;gap:9px;margin-top:13px}.form-row{display:grid;grid-template-columns:1fr 1fr;gap:8px}.form input,.form textarea,.form select{width:100%;border:1px solid var(--line);border-radius:10px;background:#09111c;color:var(--text);padding:10px;font:inherit;font-size:11px}.form textarea{min-height:70px;resize:vertical}.checks{display:flex;flex-wrap:wrap;gap:10px;color:#9bb0c3;font-size:10px}.checks label{display:flex;gap:6px;align-items:center}.action{justify-self:start;border:1px solid rgba(97,195,255,.28);background:rgba(97,195,255,.08);color:#a9dcff;border-radius:9px;padding:9px 11px;font:inherit;font-size:10px;font-weight:900;cursor:pointer}.notice{min-height:18px;color:#8ca4ba;font-size:10px;margin:8px 0}.empty{border:1px dashed var(--line);border-radius:18px;padding:36px;text-align:center;color:#8298ad}.public-link{color:#89cfff;text-decoration:none}@media(max-width:800px){.bar{flex-wrap:wrap;padding:9px 0}.brand{flex:1}nav{order:3;width:100%;margin:0}.desk,.grid{grid-template-columns:1fr}.stats{grid-template-columns:1fr 1fr}.levels{grid-template-columns:1fr 1fr}.version-grid{grid-template-columns:1fr}.form-row{grid-template-columns:1fr}}@media(max-width:430px){.shell{width:min(100% - 20px,1180px)}.stats,.levels{grid-template-columns:1fr}.hero h1{font-size:42px}}
</style></head><body><header class="top"><div class="shell bar"><div class="brand">SIGNAL <span>BRIDGE</span></div><nav>${nav(active)}</nav><span class="tier">${tier}</span><a class="logout" href="/member/logout">Log out</a></div></header><main class="shell"><section class="hero"><span class="eyebrow">Discord-linked member ${suffix}</span><h1>${escapeHtml(title)}</h1><p>${escapeHtml(subtitle)}</p></section>${content}</main>${script ? `<script>${script}</script>` : ""}</body></html>`;
}

async function dashboardData(session, env) {
  const [journal, ownedStrategies, versions] = await Promise.all([
    env.DB.prepare(`SELECT COUNT(*) AS total FROM journal_entries WHERE discord_author_id = ?1`).bind(session.discord_user_id).run(),
    env.DB.prepare(`SELECT COUNT(*) AS total FROM strategy_profiles WHERE owner_type='MEMBER' AND owner_discord_id=?1`).bind(session.discord_user_id).run(),
    env.DB.prepare(`SELECT COUNT(*) AS total FROM strategy_versions v JOIN strategy_profiles p ON p.id=v.strategy_id WHERE p.owner_type='MEMBER' AND p.owner_discord_id=?1`).bind(session.discord_user_id).run(),
  ]);
  return {
    journal: Number(journal.results?.[0]?.total || 0),
    strategies: Number(ownedStrategies.results?.[0]?.total || 0),
    versions: Number(versions.results?.[0]?.total || 0),
  };
}

async function renderDashboard(session, entitlement, env) {
  const [counts, summary] = await Promise.all([dashboardData(session, env), getSessionSummaryData(env, "MES")]);
  const latest = summary?.latest || {};
  const content = `<div class="stats"><div class="stat"><span>Journal records</span><strong>${counts.journal}</strong></div><div class="stat"><span>Your strategies</span><strong>${counts.strategies}</strong></div><div class="stat"><span>Strategy versions</span><strong>${counts.versions}</strong></div><div class="stat"><span>Latest MES stage</span><strong>${escapeHtml(latest.stage ? latest.stage.replaceAll("_", " ") : "No session")}</strong></div></div><section class="grid"><a class="card" href="/member/live"><span class="tag">Private desk</span><h3>Live Desk</h3><p>Read the stored ORB, session lifecycle, setup state and market intelligence without leaving the member app.</p><b class="link">Open Live Desk →</b></a><a class="card" href="/member/journal"><span class="tag">Your records</span><h3>My Journal</h3><p>Private Discord-linked notes, screenshots, outcomes, P&amp;L, R and review history.</p><b class="link">Open Journal →</b></a><a class="card" href="/member/strategy-lab"><span class="tag">Version control</span><h3>Strategy Lab</h3><p>Create strategy identities and preserve each rule/evidence version instead of overwriting history.</p><b class="link">Open Strategy Lab →</b></a><a class="card" href="/member/indicators"><span class="tag">Chart-tool record</span><h3>Indicator Workspace</h3><p>Attach the exact indicator version and settings to the strategy version it supports, then watch for live-version drift.</p><b class="link">Open Indicators →</b></a></section><section class="section"><div class="card"><span class="tag">Public product</span><h3>Signal Bridge preview site</h3><p>Use the public site for product explanations, education, selected evidence and shareable pages.</p><a class="public-link link" href="${PUBLIC_BASE}">Open public Signal Bridge ↗</a></div></section>`;
  return shell({ active: "home", title: "Member workspace", subtitle: "The private operating layer around your own trading: live desk, journal, strategy versions and chart-tool configuration.", session, entitlement, content });
}

function fmt(value) {
  if (value === null || value === undefined || value === "") return "—";
  const number = Number(value);
  return Number.isFinite(number) ? number.toLocaleString(undefined, { maximumFractionDigits: 2 }) : String(value);
}

async function renderLiveDesk(session, entitlement, env) {
  const [summary, intel] = await Promise.all([
    getSessionSummaryData(env, "MES"),
    getMarketIntelligenceSummary(env),
  ]);
  const latest = summary?.latest || {};
  const orb = summary?.orb || {};
  const events = Array.isArray(summary?.events) ? summary.events.slice(-12).reverse() : [];
  const calendar = intel?.calendar || {};
  const headlines = intel?.headlines || {};
  const content = `<section class="desk"><article class="card"><span class="tag">MES session</span><h3>${escapeHtml(summary?.session_date || "Waiting for session")}</h3><p>${escapeHtml(latest.note || "No production lifecycle event has been stored yet.")}</p><div class="levels"><div class="level"><span>ORH</span><strong>${fmt(orb.orb_high)}</strong></div><div class="level"><span>ORM</span><strong>${fmt(orb.orb_mid)}</strong></div><div class="level"><span>ORL</span><strong>${fmt(orb.orb_low)}</strong></div><div class="level"><span>Range</span><strong>${orb.range_points === null || orb.range_points === undefined ? "—" : `${fmt(orb.range_points)} pts`}</strong></div></div><div class="levels"><div class="level"><span>Stage</span><strong>${escapeHtml(latest.stage ? latest.stage.replaceAll("_", " ") : "—")}</strong></div><div class="level"><span>Bias</span><strong>${escapeHtml(latest.bias || "—")}</strong></div><div class="level"><span>Setup</span><strong>${escapeHtml(latest.setup || "—")}</strong></div><div class="level"><span>State</span><strong>${escapeHtml(latest.side || "WAIT")}</strong></div></div></article><aside class="card"><span class="tag">Market intelligence</span><h3>Calendar + headlines</h3><p>Calendar remains fail-closed: unavailable never means clear.</p><div class="mini" style="margin-top:12px"><span>Economic calendar</span><strong>${escapeHtml(calendar.status === "OK" && calendar.fresh ? "FRESH" : "UNAVAILABLE / STALE")}</strong></div><div class="mini" style="margin-top:8px"><span>Market headlines</span><strong>${escapeHtml(headlines.status === "OK" && headlines.fresh ? "FRESH" : "UNAVAILABLE / STALE")}</strong></div>${(headlines.items || []).slice(0,4).map((item) => `<div class="headline"><b>${escapeHtml(item.title)}</b><span>${escapeHtml(item.publisher || "Market feed")}</span></div>`).join("")}</aside></section><section class="section"><div class="section-head"><div><span class="tag">Session Story</span><h2>Stored lifecycle</h2></div><p>This is the same durable event stream the bot reads. Pine becomes the sensor; the Worker remains the memory.</p></div><div class="card">${events.length ? `<div class="timeline">${events.map((event) => `<div class="event"><b>${escapeHtml(String(event.stage || "EVENT").replaceAll("_", " "))}${event.side ? ` · ${escapeHtml(event.side)}` : ""}</b><span>${escapeHtml(event.note || event.setup || event.outcome || "Session update")}${event.indicator_version ? ` · indicator ${escapeHtml(event.indicator_version)}` : ""}</span></div>`).join("")}</div>` : `<div class="empty">No production session lifecycle yet.</div>`}</div></section>`;
  return shell({ active: "live", title: "Live Desk", subtitle: "Private session state, ORB structure, market intelligence and the stored lifecycle feeding Signal Bridge and Discord.", session, entitlement, content });
}

async function indicatorRows(session, env) {
  const versionsResult = await env.DB.prepare(
    `SELECT p.id AS strategy_id, p.owner_type, p.name AS strategy_name, p.slug,
            v.id AS version_id, v.version_label, v.evidence_stage,
            v.indicator_name, v.indicator_version, v.indicator_config_json
     FROM strategy_profiles p
     JOIN strategy_versions v ON v.strategy_id = p.id AND v.is_current = 1
     WHERE p.owner_type = 'SYSTEM' OR p.owner_discord_id = ?1
     ORDER BY p.owner_type DESC, p.updated_at DESC`,
  ).bind(session.discord_user_id).run();
  const rows = Array.isArray(versionsResult.results) ? versionsResult.results : [];
  const eventsResult = await env.DB.prepare(
    `SELECT strategy_version_id, indicator_version, stage, symbol, received_at
     FROM session_events
     WHERE stage != 'TEST' AND indicator_version IS NOT NULL
     ORDER BY received_at DESC LIMIT 250`,
  ).run();
  const latestByVersion = new Map();
  for (const event of eventsResult.results || []) {
    if (event.strategy_version_id && !latestByVersion.has(event.strategy_version_id)) latestByVersion.set(event.strategy_version_id, event);
  }
  return rows.map((row) => ({ ...row, latest_event: latestByVersion.get(row.version_id) || null }));
}

function parseConfig(value) {
  try {
    const config = JSON.parse(value || "{}");
    return config && typeof config === "object" && !Array.isArray(config) ? config : {};
  } catch {
    return {};
  }
}

function indicatorCard(row) {
  const owned = row.owner_type === "MEMBER";
  const config = parseConfig(row.indicator_config_json);
  const expected = row.indicator_version || "Not set";
  const seen = row.latest_event?.indicator_version || "No live event";
  const match = row.indicator_version && row.latest_event?.indicator_version
    ? row.indicator_version === row.latest_event.indicator_version
    : null;
  const state = match === true ? ["ok", "MATCH"] : match === false ? ["bad", "VERSION MISMATCH"] : ["warn", "AWAITING LIVE PROOF"];
  const form = owned ? `<form class="form indicator-form" data-strategy="${escapeHtml(row.strategy_id)}" data-version="${escapeHtml(row.version_id)}"><div class="form-row"><input name="indicator_name" value="${escapeHtml(row.indicator_name || "")}" placeholder="Indicator name"><input name="indicator_version" value="${escapeHtml(row.indicator_version || "")}" placeholder="Version — e.g. 1.3"></div><div class="form-row"><input name="timeframe" value="${escapeHtml(config.timeframe || "")}" placeholder="Chart timeframe — e.g. 1m"><input name="orb" value="${escapeHtml(config.orb || "")}" placeholder="ORB — e.g. 08:00–08:15 ET"></div><div class="form-row"><input name="trade_window" value="${escapeHtml(config.trade_window || "")}" placeholder="Trade window"><input name="flat_time" value="${escapeHtml(config.flat_time || "")}" placeholder="Force flat time"></div><div class="checks"><label><input type="checkbox" name="use_vwap" ${config.use_vwap ? "checked" : ""}>VWAP</label><label><input type="checkbox" name="use_ema" ${config.use_ema ? "checked" : ""}>EMA</label></div><textarea name="notes" placeholder="Preset / alert / chart notes">${escapeHtml(config.notes || "")}</textarea><button class="action" type="submit">Save indicator snapshot</button></form>` : "";
  return `<article class="strategy"><div class="strategy-top"><span class="badge ${owned ? "member" : "system"}">${owned ? "YOUR STRATEGY" : "FLAGSHIP MODEL"}</span><span class="status ${state[0]}">${state[1]}</span></div><h3>${escapeHtml(row.strategy_name)} · ${escapeHtml(row.version_label)}</h3><p>${escapeHtml(row.evidence_stage || "PROJECT_RULE")} · Keep the chart-tool snapshot attached to this exact strategy version.</p><div class="version-grid"><div class="mini"><span>Expected indicator</span><strong>${escapeHtml(row.indicator_name || "Not set")}</strong></div><div class="mini"><span>Expected version</span><strong>${escapeHtml(expected)}</strong></div><div class="mini"><span>Last live version seen</span><strong>${escapeHtml(seen)}</strong></div></div>${form}</article>`;
}

async function renderIndicators(session, entitlement, env) {
  const rows = await indicatorRows(session, env);
  const cards = rows.length ? rows.map(indicatorCard).join("") : `<div class="empty">Create a Strategy Lab version first, then attach an indicator snapshot here.</div>`;
  const content = `<section class="section"><div class="section-head"><div><span class="tag">Strategy-linked presets</span><h2>Indicator snapshots</h2></div><p>This is configuration/version control — not evidence that the indicator improves performance. Live version checks only prove what Pine version reached Signal Bridge.</p></div><div id="notice" class="notice"></div>${cards}</section>`;
  const script = `const notice=document.getElementById('notice');document.querySelectorAll('.indicator-form').forEach(form=>form.addEventListener('submit',async(e)=>{e.preventDefault();const f=new FormData(form);notice.textContent='Saving indicator snapshot…';const body={strategy_id:form.dataset.strategy,version_id:form.dataset.version,indicator_name:f.get('indicator_name'),indicator_version:f.get('indicator_version'),timeframe:f.get('timeframe'),orb:f.get('orb'),trade_window:f.get('trade_window'),flat_time:f.get('flat_time'),use_vwap:f.get('use_vwap')==='on',use_ema:f.get('use_ema')==='on',notes:f.get('notes')};try{const r=await fetch('/member/api/indicators/config',{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify(body)});const j=await r.json();if(!r.ok||!j.ok)throw new Error(j.error||'save_failed');notice.textContent='Saved. This strategy version now owns that indicator snapshot.';setTimeout(()=>location.reload(),450)}catch(err){notice.textContent='Could not save: '+err.message}}));`;
  return shell({ active: "indicators", title: "Indicator Workspace", subtitle: "Save the exact chart-tool identity and settings attached to a strategy version, then compare that expectation against the Pine version actually arriving at Signal Bridge.", session, entitlement, content, script });
}

async function saveIndicatorConfig(session, env, request) {
  let body;
  try { body = await request.json(); } catch { return json({ ok: false, error: "invalid_json" }, 400); }
  const strategyId = String(body?.strategy_id || "").slice(0, 180);
  const versionId = String(body?.version_id || "").slice(0, 180);
  if (!strategyId || !versionId) return json({ ok: false, error: "strategy_and_version_required" }, 400);
  const owned = await env.DB.prepare(
    `SELECT v.id
     FROM strategy_versions v JOIN strategy_profiles p ON p.id=v.strategy_id
     WHERE v.id=?1 AND p.id=?2 AND p.owner_type='MEMBER' AND p.owner_discord_id=?3
     LIMIT 1`,
  ).bind(versionId, strategyId, session.discord_user_id).run();
  if (!owned.results?.[0]) return json({ ok: false, error: "strategy_version_not_owned" }, 403);
  const config = {
    timeframe: String(body?.timeframe || "").slice(0, 32) || null,
    orb: String(body?.orb || "").slice(0, 64) || null,
    trade_window: String(body?.trade_window || "").slice(0, 64) || null,
    flat_time: String(body?.flat_time || "").slice(0, 32) || null,
    use_vwap: body?.use_vwap === true,
    use_ema: body?.use_ema === true,
    notes: String(body?.notes || "").slice(0, 1200) || null,
  };
  await env.DB.prepare(
    `UPDATE strategy_versions
     SET indicator_name=?2, indicator_version=?3, indicator_config_json=?4
     WHERE id=?1`,
  ).bind(
    versionId,
    String(body?.indicator_name || "").slice(0, 120) || null,
    String(body?.indicator_version || "").slice(0, 96) || null,
    JSON.stringify(config),
  ).run();
  return json({ ok: true, version_id: versionId, indicator_config: config });
}

function accessDenied(error) {
  const message = error === "premium_access_required"
    ? "Your Discord session is valid, but Signal Bridge Premium access is not active for this account."
    : "Use /member-login in the Signal Bridge Discord to generate a private one-time sign-in link.";
  return html(`<div style="font-family:system-ui;background:#05080d;color:#eaf4ff;min-height:100vh;padding:60px 24px"><div style="max-width:620px;margin:auto"><h1>Signal Bridge Premium</h1><p style="color:#8ca1b6;line-height:1.7">${escapeHtml(message)}</p><a style="color:#7ecbff" href="${PUBLIC_BASE}/access.html">Open member access</a></div></div>`, 401);
}

export async function handleMemberToolsRequest(request, env) {
  const url = new URL(request.url);
  const handled = new Set(["/member", "/member/", "/member/live", "/member/indicators", "/member/api/indicators/config"]);
  if (!handled.has(url.pathname)) return null;
  const access = await memberAccess(request, env);
  if (access.error) {
    if (url.pathname.startsWith("/member/api/")) return json({ ok: false, error: access.error }, 401);
    return accessDenied(access.error);
  }
  const { session, entitlement } = access;
  if (request.method === "GET" && (url.pathname === "/member" || url.pathname === "/member/")) return html(await renderDashboard(session, entitlement, env));
  if (request.method === "GET" && url.pathname === "/member/live") return html(await renderLiveDesk(session, entitlement, env));
  if (request.method === "GET" && url.pathname === "/member/indicators") return html(await renderIndicators(session, entitlement, env));
  if (request.method === "POST" && url.pathname === "/member/api/indicators/config") return saveIndicatorConfig(session, env, request);
  return json({ ok: false, error: "method_not_allowed" }, 405);
}
