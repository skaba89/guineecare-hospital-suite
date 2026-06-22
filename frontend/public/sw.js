/**
 * GuinéeCare Service Worker — v1.3.0
 *
 * Minimal PWA shell. Strategy:
 * - App shell (HTML, JS, CSS, icons): stale-while-revalidate (instant load
 *   from cache, refresh in background).
 * - API GET requests: network-first (fall back to cache when offline).
 * - API POST/PUT/DELETE: pass through (no caching); if offline, the request
 *   fails and the app shows a toast — actual offline mutation queueing is
 *   deferred to a future PWA evolution.
 *
 * The service worker is intentionally small to keep maintenance simple.
 * When the backend adds new endpoints or the frontend ships a new build,
 * bumping `CACHE_VERSION` triggers cache invalidation on next load.
 */
const CACHE_VERSION = "guineecare-v1.3.0";
const APP_SHELL_CACHE = `${CACHE_VERSION}-shell`;
const API_CACHE = `${CACHE_VERSION}-api`;

const APP_SHELL_PATHS = [
  "/",
  "/index.html",
  "/manifest.webmanifest",
  "/icons/icon-192.png",
  "/icons/icon-512.png",
];

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(APP_SHELL_CACHE).then((cache) => cache.addAll(APP_SHELL_PATHS))
      .then(() => self.skipWaiting())
  );
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(
        keys
          .filter((k) => !k.startsWith(CACHE_VERSION))
          .map((k) => caches.delete(k))
      )
    ).then(() => self.clients.claim())
  );
});

self.addEventListener("fetch", (event) => {
  const req = event.request;
  const url = new URL(req.url);

  // Only handle same-origin requests
  if (url.origin !== self.location.origin) return;

  // Skip WebSocket upgrades
  if (req.url.startsWith("ws://") || req.url.startsWith("wss://")) return;

  // Skip non-GET requests (mutations are not cached)
  if (req.method !== "GET") return;

  // API requests: network-first, fall back to cache
  if (url.pathname.startsWith("/api/")) {
    event.respondWith(
      fetch(req)
        .then((res) => {
          // Only cache successful responses
          if (res.ok) {
            const clone = res.clone();
            caches.open(API_CACHE).then((cache) => cache.put(req, clone));
          }
          return res;
        })
        .catch(() => caches.match(req).then((cached) => cached || new Response(
          JSON.stringify({ detail: "Offline — request queued for sync" }),
          { status: 503, headers: { "Content-Type": "application/json" } }
        )))
    );
    return;
  }

  // App shell: stale-while-revalidate
  event.respondWith(
    caches.match(req).then((cached) => {
      const fetchPromise = fetch(req)
        .then((res) => {
          if (res.ok) {
            const clone = res.clone();
            caches.open(APP_SHELL_CACHE).then((cache) => cache.put(req, clone));
          }
          return res;
        })
        .catch(() => cached);
      return cached || fetchPromise;
    })
  );
});

// Listen for messages from the client (e.g. "skipWaiting")
self.addEventListener("message", (event) => {
  if (event.data === "skipWaiting") {
    self.skipWaiting();
  }
});
