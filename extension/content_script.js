// extension/content_script.js
const SYS_ID_PATTERN = /[a-f0-9]{32}/;

let cachedTicket = null;
let userToken = null;
let lastSysId;

const userTokenPromise = new Promise((resolve) => {
  function handleMessage(event) {
    if (
      event.source === window &&
      event.origin === window.location.origin &&
      event.data &&
      event.data.source === "sn_ticket_recommender"
    ) {
      window.removeEventListener("message", handleMessage);
      resolve(event.data.g_ck);
    }
  }
  window.addEventListener("message", handleMessage);
  setTimeout(() => {
    window.removeEventListener("message", handleMessage);
    resolve(null);
  }, 3000);
});

function extractSysId(url) {
  const match = url.match(SYS_ID_PATTERN);
  return match ? match[0] : null;
}

async function fetchIncident(sysId) {
  const response = await fetch(
    `/api/now/table/incident/${sysId}?sysparm_fields=number,short_description,description`,
    { credentials: "same-origin", headers: { "X-UserToken": userToken } }
  );
  if (!response.ok) {
    throw new Error(`incident fetch failed: ${response.status}`);
  }
  const data = await response.json();
  return data.result;
}

function deepQuerySelectorAll(selector, root = document) {
  const results = [];
  const stack = [root];
  while (stack.length > 0) {
    const node = stack.pop();
    if (typeof node.querySelectorAll === "function") {
      results.push(...node.querySelectorAll(selector));
      const all = node.querySelectorAll("*");
      for (const el of all) {
        if (el.shadowRoot) {
          stack.push(el.shadowRoot);
        }
      }
    }
  }
  return results;
}

function scrapeWorkNotes() {
  const articles = deepQuerySelectorAll("article.sn-as-card");
  if (articles.length === 0) {
    return { entries: [], unavailable: true };
  }

  const entries = [];
  for (const article of articles) {
    const typeLabel = article.querySelector(".sn-as-card-header-bottom .meta");
    if (!typeLabel || typeLabel.textContent.trim() !== "Work notes") {
      continue;
    }
    const author = article.querySelector("#card-title .title-text");
    const timeEl = article.querySelector(".sn-as-card-header-bottom time");
    const bodyEl = article.querySelector(".sn-as-card-body-journal");
    entries.push({
      value: bodyEl ? bodyEl.textContent.trim() : "",
      sys_created_on: timeEl ? timeEl.textContent.trim() : "",
      sys_created_by: author ? author.textContent.trim() : "",
    });
  }
  return { entries, unavailable: false };
}

async function loadTicket(sysId) {
  if (!sysId) {
    cachedTicket = { error: "not_an_incident_page" };
    return;
  }

  userToken = await userTokenPromise;

  try {
    const incident = await fetchIncident(sysId);
    let workNotes = scrapeWorkNotes();
    if (workNotes.unavailable) {
      await new Promise((resolve) => setTimeout(resolve, 1500));
      workNotes = scrapeWorkNotes();
    }
    cachedTicket = {
      number: incident.number,
      short_description: incident.short_description,
      description: incident.description,
      work_notes: workNotes.entries,
      work_notes_unavailable: workNotes.unavailable,
    };
  } catch (err) {
    cachedTicket = { error: "incident_fetch_failed" };
  }
}

async function checkForNavigation() {
  const sysId = extractSysId(window.location.href);
  if (sysId === lastSysId) {
    return;
  }
  lastSysId = sysId;
  await loadTicket(sysId);
  chrome.runtime.sendMessage({ type: "TICKET_UPDATED", ticket: cachedTicket });
}

let loadPromise = checkForNavigation();
setInterval(checkForNavigation, 1000);

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.type === "GET_TICKET") {
    loadPromise.then(() => sendResponse(cachedTicket));
    return true;
  }
  return true;
});
