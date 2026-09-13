// extension/sidepanel.js
const BACKEND_URL = "https://servicenow.smafnanhaider.com";
const BACKEND_API_KEY = "92fe0b377b35569610c2e6e70d827d9d8f1b3e0c40d5b04f5a1bea070426044b";

const ticketHeader = document.getElementById("ticket-header");
const analyzeBtn = document.getElementById("analyze-btn");
const statusEl = document.getElementById("status");
const resultEl = document.getElementById("result");

let currentTicket = null;

function escapeHtml(text) {
  const div = document.createElement("div");
  div.textContent = text == null ? "" : String(text);
  return div.innerHTML;
}

function redactSensitiveText(text) {
  return text
    .replace(/\b(?:\d{1,3}\.){3}\d{1,3}\b/g, "[REDACTED-IP]")
    .replace(/\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b/g, "[REDACTED-EMAIL]")
    .replace(/RcpID:\s*\d+/gi, "RcpID: [REDACTED]")
    .replace(/NetID:\s*\S+/gi, "NetID: [REDACTED]")
    .replace(/\b[A-Za-z]{2,4}\d{2,4}\b/g, "[REDACTED-ID]");
}

function requestTicketFromActiveTab() {
  return new Promise((resolve) => {
    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
      if (!tabs[0]) {
        resolve(null);
        return;
      }
      const timeout = setTimeout(() => resolve(null), 8000);
      chrome.tabs.sendMessage(tabs[0].id, { type: "GET_TICKET" }, (response) => {
        clearTimeout(timeout);
        if (chrome.runtime.lastError) {
          resolve(null);
          return;
        }
        resolve(response);
      });
    });
  });
}

function renderTicketHeader(ticket) {
  if (!ticket || ticket.error === "not_an_incident_page") {
    ticketHeader.textContent = "Open a ServiceNow incident to use this panel.";
    return false;
  }
  if (ticket.error === "incident_fetch_failed") {
    ticketHeader.innerHTML = '<span class="error">Couldn\'t read ticket - check you\'re logged into ServiceNow.</span>';
    return false;
  }

  const notesLine = ticket.work_notes_unavailable
    ? "Work notes unavailable"
    : `${ticket.work_notes.length} work note entr${ticket.work_notes.length === 1 ? "y" : "ies"} found`;
  ticketHeader.innerHTML = `<strong>${escapeHtml(ticket.number)}</strong>: ${escapeHtml(ticket.short_description)}<br><small>${notesLine}</small>`;
  return true;
}

function buildTicketDescription(ticket) {
  let text = ticket.description || ticket.short_description || "";
  if (ticket.work_notes && ticket.work_notes.length > 0) {
    text += "\n\nWork notes so far:\n";
    text += ticket.work_notes
      .map((n) => `- [${n.sys_created_on}] ${n.sys_created_by}: ${n.value}`)
      .join("\n");
  }
  return redactSensitiveText(text);
}

function renderRecommendation(data) {
  if (data.insufficient_evidence) {
    resultEl.innerHTML = '<p class="error">Not enough matching KB evidence found for this ticket.</p>';
    return;
  }
  if (data.schema_error) {
    resultEl.innerHTML = '<p class="error">The recommendation engine returned an unexpected response. Try again.</p>';
    return;
  }

  const badgeClass = {
    SUPPORTED: "badge-supported",
    INFERRED: "badge-inferred",
    UNCERTAIN: "badge-uncertain",
  };

  let html = `<h3>${escapeHtml(data.issue_summary)}</h3>`;
  html += "<ol>";
  for (const step of data.resolution_steps) {
    html += `<li class="step">${escapeHtml(step.step)}<span class="badge ${badgeClass[step.grounding]}">${step.grounding}</span></li>`;
  }
  html += "</ol>";
  if (data.cited_kb_articles && data.cited_kb_articles.length > 0) {
    html += `<p><strong>Cited:</strong> ${data.cited_kb_articles.map(escapeHtml).join(", ")}</p>`;
  }
  resultEl.innerHTML = html;
}

async function onAnalyzeClick() {
  if (!currentTicket) return;
  statusEl.textContent = "Analyzing...";
  resultEl.innerHTML = "";
  analyzeBtn.disabled = true;

  try {
    const response = await fetch(`${BACKEND_URL}/recommend`, {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-API-Key": BACKEND_API_KEY },
      body: JSON.stringify({ ticket_description: buildTicketDescription(currentTicket) }),
    });
    if (!response.ok) {
      throw new Error(`backend returned ${response.status}`);
    }
    const data = await response.json();
    statusEl.textContent = "";
    renderRecommendation(data);
  } catch (err) {
    statusEl.innerHTML = "<span class=\"error\">Backend not running - start it with `python3 server.py`.</span>";
  } finally {
    analyzeBtn.disabled = false;
  }
}

async function init() {
  currentTicket = await requestTicketFromActiveTab();
  const ok = renderTicketHeader(currentTicket);
  analyzeBtn.disabled = !ok;
}

analyzeBtn.addEventListener("click", onAnalyzeClick);
chrome.runtime.onMessage.addListener((message) => {
  if (message.type === "TICKET_UPDATED") {
    currentTicket = message.ticket;
    const ok = renderTicketHeader(currentTicket);
    analyzeBtn.disabled = !ok;
    resultEl.innerHTML = "";
    statusEl.textContent = "";
  }
});
init();
