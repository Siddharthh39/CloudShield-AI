const CONFIG = window.CLOUDSHIELD_CONFIG || {};
const API_BASE_URL = CONFIG.apiBaseUrl || "http://localhost:8000";
const DEPLOYED_REDIRECT_URI = "https://cloudshield-ai-frontendbucket-4a5k1chva3c5.s3.ap-south-1.amazonaws.com/index.html";
const TOKEN_KEY = "cloudshield_access_token";
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
  const headers = { "Content-Type": "application/json", ...(options.headers || {}) };
  const token = sessionStorage.getItem(TOKEN_KEY);
  if (token) headers.Authorization = "Bearer " + token;
  const response = await fetch(`${API_BASE_URL}${path}`, { ...options, headers });
  if (response.status === 401) {
    showLogin("Your session has expired. Please sign in again.");
    throw new Error("Authentication required");
  }
  if (!response.ok) throw new Error(await response.text() || `Request failed with ${response.status}`);
  return response.json();
}

function showLogin(message = "") {
  document.body.classList.add("logged-out");
  byId("loginError").textContent = message;
}
function showApp() {
  document.body.classList.remove("logged-out");
  const token = sessionStorage.getItem(TOKEN_KEY);
  if (token) {
    try {
      const payload = JSON.parse(atob(token.split(".")[1]));
      byId("userAvatar").textContent = (payload.email || payload.username || "CS").slice(0, 2).toUpperCase();
      const groups = payload["cognito:groups"] || payload.groups || [];
      const isAdmin = groups.includes("Admin") || payload.email === "hellosiddharthh@gmail.com";
      byId("roleBadge").textContent = isAdmin ? "Admin" : "Client";
      if (isAdmin) {
        byId("adminPanel").hidden = false;
        loadAdminQueue();
      }
    } catch { byId("userAvatar").textContent = "CS"; }
  }
}
async function loadAdminQueue() {
  try {
    const pending = await api("/admin/sites");
    byId("adminQueue").innerHTML = pending.length ? pending.map(site => `<div class="admin-row"><span><strong>${escapeHtml(site.name)}</strong><small>${escapeHtml(site.url)}</small></span><button data-approve-id="${site.id}">Approve</button></div>`).join("") : "<small>No sites waiting for approval.</small>";
    byId("adminQueue").querySelectorAll("[data-approve-id]").forEach(button => button.addEventListener("click", async () => {
      await api(`/admin/sites/${button.dataset.approveId}/approve`, { method: "POST" });
      await loadSites();
      loadAdminQueue();
    }));
  } catch (error) {
    byId("adminQueue").textContent = error.message;
  }
}
function base64Url(bytes) {
  return btoa(String.fromCharCode(...new Uint8Array(bytes))).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
}
function getRedirectUri() {
  return CONFIG.redirectUri || DEPLOYED_REDIRECT_URI;
}
function oauthUrl() {
  const redirectUri = getRedirectUri();
  const state = crypto.randomUUID();
  sessionStorage.setItem("cloudshield_oauth_state", state);
  return `${CONFIG.cognitoDomain}/oauth2/authorize?client_id=${encodeURIComponent(CONFIG.cognitoClientId)}&response_type=code&scope=openid+email+profile&redirect_uri=${encodeURIComponent(redirectUri)}&state=${state}`;
}
async function exchangeCode(code) {
  const redirectUri = getRedirectUri();
  const body = new URLSearchParams({ grant_type: "authorization_code", client_id: CONFIG.cognitoClientId, code, redirect_uri: redirectUri });
  const response = await fetch(`${CONFIG.cognitoDomain}/oauth2/token`, { method: "POST", headers: { "Content-Type": "application/x-www-form-urlencoded" }, body });
  if (!response.ok) throw new Error("Cognito sign-in could not be completed.");
  const tokens = await response.json();
  sessionStorage.setItem(TOKEN_KEY, tokens.access_token);
  window.history.replaceState({}, "", window.location.pathname);
}
async function initializeAuth() {
  const params = new URLSearchParams(window.location.search);
  if (params.get("error")) throw new Error(params.get("error_description") || "Cognito sign-in was cancelled.");
  if (params.get("code")) {
    const state = sessionStorage.getItem("cloudshield_oauth_state");
    if (state !== params.get("state")) throw new Error("The Cognito sign-in state did not match.");
    await exchangeCode(params.get("code"));
  }
  if (CONFIG.cognitoDomain && CONFIG.cognitoClientId) {
    if (!sessionStorage.getItem(TOKEN_KEY)) showLogin();
    else showApp();
  } else {
    byId("loginButton").hidden = true;
    byId("demoButton").hidden = false;
    showLogin("Cognito is not configured; use the local seeded demo.");
  }
}

function renderSites() {
  byId("siteTotal").textContent = `${sites.length} site${sites.length === 1 ? "" : "s"}`;
  const findingCount = sites.reduce((total, site) => total + (site.latest_scan?.findings || []).filter(finding => finding.status === "open").length, 0);
  byId("navFindingCount").textContent = findingCount;
  byId("statSites").textContent = sites.length;
  byId("statFindings").textContent = findingCount;
  byId("statPending").textContent = sites.filter(site => site.approval_status !== "approved").length;
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
  return findings.map((finding, index) => `<article class="finding"><div class="finding-top"><h4>${escapeHtml(finding.title)}</h4><span class="severity ${escapeHtml(finding.severity)}">${escapeHtml(finding.severity)}</span></div><p>${escapeHtml(finding.description)}</p><div class="finding-recommendation">${escapeHtml(finding.recommendation)}</div><button class="ai-explain" data-finding-index="${index}">Threat assessment with Gemini</button><div class="ai-result" id="aiResult${index}"></div></article>`).join("");
}
function logMarkup(events) {
  if (!events.length) return `<div class="empty-state">No representative log events in this scan.</div>`;
  return events.map(event => `<div class="log-row"><span class="log-severity ${escapeHtml(event.severity)}"></span><span class="log-method">${escapeHtml(event.method)}</span><span class="log-path">${escapeHtml(event.path)}</span><span class="log-code ${event.status_code >= 400 ? "blocked" : ""}">${escapeHtml(event.status_code)}</span><span class="log-action">${escapeHtml(event.action)}</span></div>`).join("");
}
function renderDetail(site) {
  const scan = site.latest_scan || { findings: [], log_events: [], request_count: 0, blocked_count: 0, duration_ms: 0, log_count: 0 };
  const openFindings = (scan.findings || []).filter(finding => finding.status === "open");
  const approval = site.approval_status === "approved"
    ? `<button class="scan-now" data-site-id="${site.id}">Run passive diagnostics</button>`
    : `<span class="pending-badge">Pending administrator approval</span><button class="refresh-site" data-site-id="${site.id}">Refresh approval status</button>`;
  byId("detailPanel").innerHTML = `<div class="detail-panel">
    <div class="detail-header"><div><p class="eyebrow">Current analysis</p><h2>${escapeHtml(site.name)}</h2><div class="detail-url">${escapeHtml(site.url)}</div></div><div class="grade-box"><strong>${escapeHtml(site.grade)}</strong><div><small>Risk grade</small><small>${escapeHtml(site.status)} posture</small></div></div></div>
    <div class="summary-line">${escapeHtml(site.summary)} ${approval}</div>
    <div class="metrics"><div class="metric metric-risk"><div class="metric-label">Risk score</div><div class="metric-value ${site.risk_score < 30 ? "low" : site.risk_score < 60 ? "medium" : ""}">${site.risk_score}</div><div class="metric-note">out of 100</div></div><div class="metric"><div class="metric-label">Requests analyzed</div><div class="metric-value">${formatNumber(scan.request_count)}</div><div class="metric-note">${formatNumber(scan.log_count)} log events</div></div><div class="metric"><div class="metric-label">Blocked signals</div><div class="metric-value">${formatNumber(scan.blocked_count)}</div><div class="metric-note">edge decisions</div></div><div class="metric"><div class="metric-label">Scan duration</div><div class="metric-value">${(scan.duration_ms / 1000).toFixed(1)}s</div><div class="metric-note">completed ${formatTime(scan.started_at)}</div></div></div>
    <div id="findings"><div class="section-title"><h3>Priority findings</h3><span>${openFindings.length} open issue${openFindings.length === 1 ? "" : "s"}</span></div><div class="findings-list">${findingMarkup(openFindings)}</div></div>
    <div id="logs" style="margin-top:25px"><div class="section-title"><h3>Log intelligence</h3><span>${escapeHtml(site.technology || "Web application")} · ${escapeHtml(site.region || "Unknown region")}</span></div><div class="telemetry-panel">${logMarkup(scan.log_events || [])}</div></div>
  </div>`;
  byId("detailPanel").querySelectorAll(".ai-explain").forEach(button => button.addEventListener("click", async () => {
    const finding = openFindings[Number(button.dataset.findingIndex)];
    const result = byId(`aiResult${button.dataset.findingIndex}`);
    button.disabled = true;
    result.textContent = "Generating an evidence-grounded explanation...";
    try {
      const ai = await api("/ai/explain", { method: "POST", body: JSON.stringify(finding) });
      result.innerHTML = `<strong>AI explanation</strong><p>${escapeHtml(ai.explanation)}</p><strong>Recommendation</strong><p>${escapeHtml(ai.recommendation)}</p>`;
    } catch (error) {
      result.textContent = error.message;
    } finally { button.disabled = false; }
  }));
  const scanButton = byId("detailPanel").querySelector(".scan-now");
  if (scanButton) scanButton.addEventListener("click", () => runPassiveScan(site.id));
  const refreshButton = byId("detailPanel").querySelector(".refresh-site");
  if (refreshButton) refreshButton.addEventListener("click", loadSites);
}
function selectSite(siteId) { selectedSiteId = siteId; const site = sites.find(item => item.id === siteId); if (!site) return; byId("urlInput").value = site.url.replace(/^https?:\/\//, ""); renderSites(); renderDetail(site); }
async function loadSites() {
  try { sites = await api("/sites"); renderSites(); if (sites.length) selectSite(selectedSiteId && sites.some(site => site.id === selectedSiteId) ? selectedSiteId : sites[0].id); else byId("detailPanel").innerHTML = `<div class="loading-state large">Enter a URL above to begin your first analysis.</div>`; }
  catch (error) { byId("siteList").innerHTML = `<div class="empty-state">Unable to connect to the analysis API.</div>`; byId("detailPanel").innerHTML = `<div class="loading-state large">${escapeHtml(error.message)}</div>`; }
}
async function analyzeSite(event) {
  event.preventDefault(); const input = byId("urlInput"); const button = byId("scanButton"); const value = input.value.trim(); if (!value) return; button.disabled = true; setFormStatus("Registering target for administrator approval...");
  try { const site = await api("/sites/register", { method: "POST", body: JSON.stringify({ url: value }) }); sites.unshift(site); selectedSiteId = site.id; renderSites(); renderDetail(site); setFormStatus("Registration submitted · awaiting administrator approval"); }
  catch (error) { setFormStatus(error.message.replace(/[{}\"]/g, ""), true); }
  finally { button.disabled = false; }
}
async function runPassiveScan(siteId) {
  setFormStatus("Running passive HTTPS, TLS, and header diagnostics...");
  try {
    const site = await api(`/sites/${siteId}/scan`, { method: "POST" });
    sites = sites.map(item => item.id === site.id ? site : item);
    selectedSiteId = site.id; renderSites(); renderDetail(site); setFormStatus("Passive diagnostics complete · findings updated");
  } catch (error) { setFormStatus(error.message.replace(/[{}\"]/g, ""), true); }
}
byId("scanForm").addEventListener("submit", analyzeSite);
byId("loginButton").addEventListener("click", () => { window.location.href = oauthUrl(); });
byId("demoButton").addEventListener("click", () => { sessionStorage.removeItem(TOKEN_KEY); showApp(); loadSites(); });
byId("logoutButton").addEventListener("click", () => {
  sessionStorage.removeItem(TOKEN_KEY);
  if (CONFIG.cognitoDomain) window.location.href = `${CONFIG.cognitoDomain}/logout?client_id=${encodeURIComponent(CONFIG.cognitoClientId)}&logout_uri=${encodeURIComponent(window.location.href)}`;
  else showLogin();
});
byId("refreshAdminButton").addEventListener("click", loadAdminQueue);
initializeAuth().then(() => {
  if (!document.body.classList.contains("logged-out")) loadSites();
}).catch(error => showLogin(error.message));