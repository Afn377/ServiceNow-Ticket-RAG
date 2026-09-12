// extension/content_script.js
const SYS_ID_PATTERN = /[a-f0-9]{32}/;

let cachedTicket = null;
let userToken = null;

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

async function fetchWorkNotes(sysId) {
  const query = `element_id=${sysId}^element=work_notes^ORDERBYsys_created_on`;
  const response = await fetch(
    `/api/now/table/sys_journal_field?sysparm_query=${encodeURIComponent(query)}&sysparm_fields=value,sys_created_on,sys_created_by`,
    { credentials: "same-origin", headers: { "X-UserToken": userToken } }
  );
  if (!response.ok) {
    return { entries: [], unavailable: true };
  }
  const data = await response.json();
  return { entries: data.result, unavailable: false };
}

async function loadTicket() {
  const sysId = extractSysId(window.location.href);
  if (!sysId) {
    cachedTicket = { error: "not_an_incident_page" };
    return;
  }

  userToken = await userTokenPromise;

  try {
    const incident = await fetchIncident(sysId);
    const workNotes = await fetchWorkNotes(sysId);
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

let loadPromise = loadTicket();

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.type === "GET_TICKET") {
    loadPromise.then(() => sendResponse(cachedTicket));
    return true;
  }
  return true;
});
