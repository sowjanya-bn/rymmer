// RYM Collector — background service worker
// Minimal: just keeps the extension alive; badge logic is handled in content.js

chrome.runtime.onInstalled.addListener(() => {
  console.log("[RYM Collector] Extension installed.");
});
