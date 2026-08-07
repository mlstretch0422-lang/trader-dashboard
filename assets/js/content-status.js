const STATUS_ORDER = ["VERIFIED", "TESTING", "UNTESTED", "RETIRED"];

const state = {
  data: null,
  search: "",
  status: "ALL",
  category: "ALL",
};

function escapeHtml(value = "") {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function countByStatus(items) {
  return STATUS_ORDER.reduce((acc, status) => {
    acc[status] = items.filter((item) => item.status === status).length;
    return acc;
  }, {});
}

function renderCounts(items) {
  const counts = countByStatus(items);
  document.getElementById("countGrid").innerHTML = STATUS_ORDER.map((status) => `
    <div class="countCard">
      <span>${escapeHtml(status)}</span>
      <strong>${counts[status] ?? 0}</strong>
    </div>
  `).join("");
}

function renderCategories(items) {
  const select = document.getElementById("categoryFilter");
  const categories = [...new Set(items.map((item) => item.category).filter(Boolean))].sort();
  select.innerHTML = ["<option value=\"ALL\">All categories</option>"]
    .concat(categories.map((category) => `<option value="${escapeHtml(category)}">${escapeHtml(category)}</option>`))
    .join("");
}

function renderSources(sources = []) {
  if (!sources.length) return "<span>No source recorded.</span>";
  return `<ul class="sourceList">${sources.map((source) => `<li><code>${escapeHtml(source)}</code></li>`).join("")}</ul>`;
}

function renderRequirements(requirements = []) {
  if (!requirements.length) return "<span>No additional test requirements recorded.</span>";
  return `<ul class="requirementList">${requirements.map((item) => `<li>${escapeHtml(item)}</li>`).join("")}</ul>`;
}

function itemMatches(item) {
  const text = [item.name, item.claim, item.note, item.category, ...(item.sources || [])]
    .join(" ")
    .toLowerCase();

  const searchOk = !state.search || text.includes(state.search);
  const statusOk = state.status === "ALL" || item.status === state.status;
  const categoryOk = state.category === "ALL" || item.category === state.category;

  return searchOk && statusOk && categoryOk;
}

function renderRegistry() {
  const items = (state.data?.items || []).filter(itemMatches);
  const registry = document.getElementById("registry");
  const resultCount = document.getElementById("resultCount");

  resultCount.textContent = `${items.length} of ${state.data?.items?.length || 0} records shown`;

  if (!items.length) {
    registry.innerHTML = '<div class="empty">No records match the current filters.</div>';
    return;
  }

  registry.innerHTML = items.map((item) => `
    <article class="item" data-status="${escapeHtml(item.status)}">
      <div class="itemHeader">
        <div>
          <h3>${escapeHtml(item.name)}</h3>
          <div class="itemClaim">${escapeHtml(item.claim)}</div>
        </div>
        <div class="badges">
          <span class="badge ${escapeHtml(item.status)}">${escapeHtml(item.status)}</span>
          <span class="badge evidence">${escapeHtml(item.evidence_level)}</span>
          <span class="badge">${escapeHtml(item.category || "uncategorized")}</span>
        </div>
      </div>
      ${item.note ? `<div class="itemClaim"><strong>Evidence note:</strong> ${escapeHtml(item.note)}</div>` : ""}
      <div class="meta">
        <div class="metaBlock">
          <strong>Source records</strong>
          ${renderSources(item.sources)}
        </div>
        <div class="metaBlock">
          <strong>Promotion requirements</strong>
          ${renderRequirements(item.test_requirements)}
        </div>
      </div>
    </article>
  `).join("");
}

function bindControls() {
  document.getElementById("searchInput").addEventListener("input", (event) => {
    state.search = event.target.value.trim().toLowerCase();
    renderRegistry();
  });

  document.getElementById("statusFilter").addEventListener("change", (event) => {
    state.status = event.target.value;
    renderRegistry();
  });

  document.getElementById("categoryFilter").addEventListener("change", (event) => {
    state.category = event.target.value;
    renderRegistry();
  });
}

async function loadRegistry() {
  const registry = document.getElementById("registry");
  try {
    const response = await fetch("./data/content-status.json", { cache: "no-store" });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);

    state.data = await response.json();
    document.getElementById("schemaVersion").textContent = state.data.schema_version || "unknown";
    document.getElementById("updatedAt").textContent = state.data.updated_at || "unknown";
    document.getElementById("promotionRule").textContent = state.data.policy?.promotion_rule || "No promotion rule recorded.";
    document.getElementById("performanceRule").textContent = state.data.policy?.performance_rule || "No performance rule recorded.";

    renderCounts(state.data.items || []);
    renderCategories(state.data.items || []);
    renderRegistry();
  } catch (error) {
    registry.innerHTML = `<div class="error">Unable to load the evidence registry: ${escapeHtml(error.message)}</div>`;
  }
}

bindControls();
loadRegistry();
