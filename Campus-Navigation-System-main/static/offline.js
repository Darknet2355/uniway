/*
  offline.js — Shared across every page.
  1. Registers the service worker (enables offline caching)
  2. Shows/hides a banner when the connection drops or comes back
  3. Exposes `window.KYU_OFFLINE` as a live boolean other scripts can check
*/

window.KYU_OFFLINE = !navigator.onLine;

// ── Register service worker ───────────────────────────────────────────────────
if ("serviceWorker" in navigator) {
  window.addEventListener("load", () => {
    // Registered from the root path (not /static/) so its scope covers the
    // whole site — /, /home, /result, /assistant, /firstday all get cached.
    navigator.serviceWorker.register("/service-worker.js", { scope: "/" })
      .then((reg) => console.log("[KYU] Service worker registered:", reg.scope))
      .catch((err) => console.warn("[KYU] Service worker registration failed:", err));
  });
}

// ── Offline banner (injected into every page automatically) ──────────────────
function createOfflineBanner() {
  if (document.getElementById("kyuOfflineBanner")) return;

  const banner = document.createElement("div");
  banner.id = "kyuOfflineBanner";
  banner.innerHTML = `
    <i class="fas fa-wifi-slash" style="margin-right:8px"></i>
    <span>You're offline — using saved campus data. Some features like AI chat need internet.</span>
  `;
  banner.style.cssText = `
    position: fixed; top: 0; left: 0; right: 0; z-index: 99999;
    background: #d97706; color: white; font-family: 'Segoe UI', sans-serif;
    font-size: 0.82rem; font-weight: 600; text-align: center;
    padding: 10px 16px; box-shadow: 0 2px 10px rgba(0,0,0,0.2);
    transform: translateY(-100%); transition: transform 0.3s ease;
  `;
  document.body.appendChild(banner);
  return banner;
}

function updateOfflineBanner() {
  let banner = document.getElementById("kyuOfflineBanner");
  if (!banner) banner = createOfflineBanner();

  window.KYU_OFFLINE = !navigator.onLine;

  if (window.KYU_OFFLINE) {
    banner.style.transform = "translateY(0)";
  } else {
    banner.style.transform = "translateY(-100%)";
  }

  // Let other scripts on the page react (e.g. assistant.html disabling
  // the send button, result.html showing a routing-source note)
  window.dispatchEvent(new CustomEvent("kyu-connectivity-change", {
    detail: { offline: window.KYU_OFFLINE }
  }));
}

window.addEventListener("online", updateOfflineBanner);
window.addEventListener("offline", updateOfflineBanner);
document.addEventListener("DOMContentLoaded", updateOfflineBanner);
