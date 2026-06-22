/*
  service-worker.js — Offline-first cache for KYU Campus Navigator

  WHAT THIS CACHES:
  1. App shell (HTML pages, so the app loads with zero network)
  2. /api/destinations (so destination lookup works offline)
  3. OpenStreetMap tiles (cached as you browse — once you've viewed a map
     area while online, it's available offline from then on)

  WHAT STAYS ONLINE-ONLY (by design):
  - /api/route (live OSRM routing) — falls back to straight-line distance
    when offline, which app.py and result.html already handle
  - /api/assistant and /api/ai-tip (Gemini AI) — these genuinely need a
    live connection; the assistant page shows a clear offline message
    instead of pretending to work

  CACHE STRATEGY:
  - App shell + destinations data: "cache first, update in background"
    (instant load, always tries to refresh from network for next time)
  - Map tiles: "cache first, network fallback" (once cached, always
    available offline; new tiles still get fetched and cached when online)
*/

const CACHE_VERSION = "kyu-nav-v1";
const SHELL_CACHE = `${CACHE_VERSION}-shell`;
const TILE_CACHE = `${CACHE_VERSION}-tiles`;
const DATA_CACHE = `${CACHE_VERSION}-data`;

// Core pages and assets needed for the app to function with zero network.
// These are cached immediately when the service worker installs.
const SHELL_URLS = [
  "/",
  "/home",
  "/assistant",
  "/firstday",
  "/static/logo.png",
  "https://unpkg.com/leaflet@1.9.4/dist/leaflet.css",
  "https://unpkg.com/leaflet@1.9.4/dist/leaflet.js",
  "https://unpkg.com/leaflet.locatecontrol@0.79.0/dist/L.Control.Locate.min.css",
  "https://unpkg.com/leaflet.locatecontrol@0.79.0/dist/L.Control.Locate.min.js",
  "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css",
];

// ─────────────────────────────────────────────────────────────────────────────
//  INSTALL — pre-cache the app shell
// ─────────────────────────────────────────────────────────────────────────────
self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(SHELL_CACHE).then((cache) => {
      // addAll fails the whole install if even one URL 404s, so we cache
      // each one individually and just log failures instead of blocking.
      return Promise.all(
        SHELL_URLS.map((url) =>
          cache.add(url).catch((err) => console.warn(`[SW] Failed to cache ${url}:`, err))
        )
      );
    })
  );
  self.skipWaiting();
});

// ─────────────────────────────────────────────────────────────────────────────
//  ACTIVATE — clean up old cache versions
// ─────────────────────────────────────────────────────────────────────────────
self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(
        keys
          .filter((key) => key.startsWith("kyu-nav-") && !key.startsWith(CACHE_VERSION))
          .map((key) => caches.delete(key))
      )
    )
  );
  self.clients.claim();
});

// ─────────────────────────────────────────────────────────────────────────────
//  FETCH — route each request to the right caching strategy
// ─────────────────────────────────────────────────────────────────────────────
self.addEventListener("fetch", (event) => {
  const url = new URL(event.request.url);

  // Map tiles — cache-first, fetch+cache in background for next time
  if (url.hostname.endsWith("tile.openstreetmap.org")) {
    event.respondWith(cacheFirstTiles(event.request));
    return;
  }

  // Destinations JSON — cache-first with background refresh
  if (url.pathname === "/api/destinations") {
    event.respondWith(cacheFirstWithRefresh(event.request, DATA_CACHE));
    return;
  }

  // Live AI / routing endpoints — always try network, never fake a cached
  // response, since stale AI replies or stale routes would be misleading.
  if (url.pathname.startsWith("/api/assistant") ||
      url.pathname.startsWith("/api/ai-tip") ||
      url.pathname.startsWith("/api/route")) {
    event.respondWith(
      fetch(event.request).catch(() =>
        new Response(
          JSON.stringify({ error: "offline", offline: true }),
          { headers: { "Content-Type": "application/json" } }
        )
      )
    );
    return;
  }

  // App shell pages (/, /home, /assistant, /firstday) — cache-first,
  // refresh in background. /result is excluded since it's dynamic per
  // destination and handled by its own query-param logic in result.html.
  if (event.request.method === "GET" && url.pathname !== "/result") {
    event.respondWith(cacheFirstWithRefresh(event.request, SHELL_CACHE));
    return;
  }

  // Everything else (POST /result fallback, etc.) — network only
  event.respondWith(
    fetch(event.request).catch(() =>
      new Response("<h1>Offline</h1><p>This action needs an internet connection.</p>", {
        headers: { "Content-Type": "text/html" },
      })
    )
  );
});

// ─────────────────────────────────────────────────────────────────────────────
//  Strategy: cache-first, then refresh cache from network in the background
// ─────────────────────────────────────────────────────────────────────────────
async function cacheFirstWithRefresh(request, cacheName) {
  const cache = await caches.open(cacheName);
  const cached = await cache.match(request);

  const networkFetch = fetch(request)
    .then((response) => {
      if (response.ok) cache.put(request, response.clone());
      return response;
    })
    .catch(() => null);

  // Return cached immediately if we have it; otherwise wait for network
  return cached || (await networkFetch) || new Response(
    "<h1>Offline</h1><p>This page hasn't been cached yet. Visit it once while online.</p>",
    { headers: { "Content-Type": "text/html" } }
  );
}

// ─────────────────────────────────────────────────────────────────────────────
//  Strategy: cache-first for map tiles, network fallback, cache what we fetch
// ─────────────────────────────────────────────────────────────────────────────
async function cacheFirstTiles(request) {
  const cache = await caches.open(TILE_CACHE);
  const cached = await cache.match(request);
  if (cached) return cached;

  try {
    const response = await fetch(request);
    if (response.ok) cache.put(request, response.clone());
    return response;
  } catch (e) {
    // No cached tile and no network — return a transparent 1x1 PNG so the
    // map doesn't show broken-image icons, just blank tiles offline.
    const blankTile =
      "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII=";
    const blob = await (await fetch(blankTile)).blob();
    return new Response(blob, { headers: { "Content-Type": "image/png" } });
  }
}
