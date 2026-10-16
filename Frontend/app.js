const API_BASE_URL = "http://localhost:8000";
let sites = [];
let selectedSiteId = null;
const byId = id => document.getElementById(id);

function escapeHtml(value) {
  return String(value ?? "").replace(/[&<>'"]/g, character => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", "'": "&#039;", '"': "&quot;" }[character]));
}
function formatNumber(value) { return new Intl.NumberFormat().format(value || 0); }
function formatTime(value) { return value ? new Date(value).toLocaleString([], { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" }) : "Not available"; }
function setFormStatus(message, isError = false) { const status = byId("formStatus"); status.textContent = message; status.style.color = isError ? "#ffaaa7" : "#aac1c0"; }

async function api(path, options = {}) {
  const response = await fetch(`${API_BASE_URL}${path}`, { headers: { "Content-Type": "application/json" }, ...options });
  if (!response.ok) throw new Error(await response.text() || `Request failed with ${response.status}`);
  return response.json();
}

function renderSites() {
  byId("siteTotal").textContent = `${sites.length} site${sites.length === 1 ? "" : "s"}`;
  const findingCount = sites.reduce((total, site) => total + (site.latest_scan?.findings || []).filter(finding => finding.status === "open").length, 0);
  byId("navFindingCount").textContent = findingCount;
  byId("siteList").innerHTML = sites.length ? sites.map(site => `
    <article class="site-card ${site.id === selectedSiteId ? "selected" : ""}" data-site-id="${site.id}" tabindex="0" role="button" aria-label="Inspect ${escapeHtml(site.name)}">
      <div class="site-card-top"><div><div class="site-name">${escapeHtml(site.name)}</div><div class="site-url">${escapeHtml(site.url.replace(/^https?:\/\//, ""))}</div></div><span class="risk-dot ${escapeHtml(site.status)}"></span></div>
      <div class="site-card-bottom"><span class="status-label"><span class="risk-dot ${escapeHtml(site.status)}"></span>${escapeHtml(site.status)}</span><span class="score-mini">${site.risk_score}<small> / 100</small></span></div>
    </article>`).join("") : `<div class="empty-state">No sites have been analyzed yet.</div>`;
  document.querySelectorAll(".site-card").forEach(card => {
    card.addEventListener("click", () => selectSite(Number(card.dataset.siteId)));
    card.addEventListener("keydown", event => { if (event.key === "Enter") selectSite(Number(card.dataset.siteId)); });
  });
}
function findingMarkup(findings) {
  if (!findings.length) return `<div class="empty-state">No open findings in this scan.</div>`;
  return findings.map(finding => `<article class="finding"><div class="finding-top"><h4>${escapeHtml(finding.title)}</h4><span class="severity ${escapeHtml(finding.severity)}">${escapeHtml(finding.severity)}</span></div><p>${escapeHtml(finding.description)}</p><div class="finding-recommendation">${escapeHtml(finding.recommendation)}</div></article>`).join("");
}
function logMarkup(events) {
  if (!events.length) return `<div class="empty-state">No representative log events in this scan.</div>`;
  return events.map(event => `<div class="log-row"><span class="log-severity ${escapeHtml(event.severity)}"></span><span class="log-method">${escapeHtml(event.method)}</span><span class="log-path">${escapeHtml(event.path)}</span><span class="log-code ${event.status_code >= 400 ? "blocked" : ""}">${escapeHtml(event.status_code)}</span><span class="log-action">${escapeHtml(event.action)}</span></div>`).join("");
}
function renderDetail(site) {
  const scan = site.latest_scan || { findings: [], log_events: [], request_count: 0, blocked_count: 0, duration_ms: 0, log_count: 0 };
  const openFindings = (scan.findings || []).filter(finding => finding.status === "open");
  byId("detailPanel").innerHTML = `<div class="detail-panel">
    <div class="detail-header"><div><p class="eyebrow">Current analysis</p><h2>${escapeHtml(site.name)}</h2><div class="detail-url">${escapeHtml(site.url)}</div></div><div class="grade-box"><strong>${escapeHtml(site.grade)}</strong><div><small>Risk grade</small><small>${escapeHtml(site.status)} posture</small></div></div></div>
    <div class="summary-line">${escapeHtml(site.summary)}</div>
    <div class="metrics"><div class="metric metric-risk"><div class="metric-label">Risk score</div><div class="metric-value ${site.risk_score < 30 ? "low" : site.risk_score < 60 ? "medium" : ""}">${site.risk_score}</div><div class="metric-note">out of 100</div></div><div class="metric"><div class="metric-label">Requests analyzed</div><div class="metric-value">${formatNumber(scan.request_count)}</div><div class="metric-note">${formatNumber(scan.log_count)} log events</div></div><div class="metric"><div class="metric-label">Blocked signals</div><div class="metric-value">${formatNumber(scan.blocked_count)}</div><div class="metric-note">edge decisions</div></div><div class="metric"><div class="metric-label">Scan duration</div><div class="metric-value">${(scan.duration_ms / 1000).toFixed(1)}s</div><div class="metric-note">completed ${formatTime(scan.started_at)}</div></div></div>
    <div id="findings"><div class="section-title"><h3>Priority findings</h3><span>${openFindings.length} open issue${openFindings.length === 1 ? "" : "s"}</span></div><div class="findings-list">${findingMarkup(openFindings)}</div></div>
    <div id="logs" style="margin-top:25px"><div class="section-title"><h3>Log intelligence</h3><span>${escapeHtml(site.technology || "Web application")} · ${escapeHtml(site.region || "Unknown region")}</span></div><div class="telemetry-panel">${logMarkup(scan.log_events || [])}</div></div>
  </div>`;
}
function selectSite(siteId) { selectedSiteId = siteId; const site = sites.find(item => item.id === siteId); if (!site) return; byId("urlInput").value = site.url.replace(/^https?:\/\//, ""); renderSites(); renderDetail(site); }
async function loadSites() {
  try { sites = await api("/sites"); renderSites(); if (sites.length) selectSite(selectedSiteId && sites.some(site => site.id === selectedSiteId) ? selectedSiteId : sites[0].id); else byId("detailPanel").innerHTML = `<div class="loading-state large">Enter a URL above to begin your first analysis.</div>`; }
  catch (error) { byId("siteList").innerHTML = `<div class="empty-state">Unable to connect to the analysis API.</div>`; byId("detailPanel").innerHTML = `<div class="loading-state large">${escapeHtml(error.message)}</div>`; }
}
async function analyzeSite(event) {
  event.preventDefault(); const input = byId("urlInput"); const button = byId("scanButton"); const value = input.value.trim(); if (!value) return; button.disabled = true; setFormStatus("Processing traffic signals and building a baseline...");
  try { const site = await api("/sites/analyze", { method: "POST", body: JSON.stringify({ url: value }) }); if (!sites.some(item => item.id === site.id)) sites.unshift(site); else sites = sites.map(item => item.id === site.id ? site : item); selectedSiteId = site.id; renderSites(); renderDetail(site); setFormStatus("Analysis complete · baseline refreshed"); }
  catch (error) { setFormStatus(error.message.replace(/[{}\"]/g, ""), true); }
  finally { button.disabled = false; }
}
byId("scanForm").addEventListener("submit", analyzeSite);
loadSites();