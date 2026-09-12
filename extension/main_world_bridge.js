// extension/main_world_bridge.js
// Runs in the page's own MAIN world (unlike content_script.js, which runs
// isolated) so it can read ServiceNow's window.g_ck CSRF token directly.
// Relays it to the isolated-world content script via postMessage, since
// MAIN and ISOLATED worlds share the DOM (and window.postMessage) even
// though they don't share JS variables.
window.postMessage(
  { source: "sn_ticket_recommender", g_ck: window.g_ck },
  window.location.origin
);
