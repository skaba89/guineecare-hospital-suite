/**
 * GuinéeCare Service Worker — v2.8.6
 *
 * v2.8.6 — FIX CRITIQUE : le service worker cassait les pages après
 * chaque déploiement. Il servait les vieux index.html + assets JS
 * depuis le cache (stale-while-revalidate) → les vieux hashes JS
 * n'existaient plus sur le serveur → 404 → pages blanches.
 *
 * Nouvelle stratégie :
 * - index.html : NETWORK-FIRST (toujours la dernière version du serveur)
 * - /assets/*.js, *.css : CACHE-FIRST (fichiers hashés, immuables —
 *   si le hash change, c'est un nouveau fichier référencé par le
 *   nouveau index.html qui est network-first)
 * - API GET : network-first, fallback cache (offline)
 * - API POST/PUT/DELETE : pas de cache
 * - Autres (icons, manifest) : stale-while-revalidate
 *
 * Le cache est invalidé à chaque changement de CACHE_VERSION.
 */
const CACHE_VERSION = "guineecare-v2.8.6";
const SHELL_CACHE = `${CACHE_VERSION}-shell`;
const API_CACHE = `${CACHE_VERSION}-api`;

self.addEventListener("install", (event) => {
  // v2.8.6 — skipWaiting immédiat pour activer le nouveau SW tout de suite
  self.skipWaiting();
  event.waitUntil(
    caches.open(SHELL_CACHE).then((cache) =>
      cache.addAll(["/manifest.webmanifest"]).catch(() => {})
    )
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

  // Skip non-GET requests
  if (req.method !== "GET") return;

  // API requests: network-first, fall back to cache
  if (url.pathname.startsWith("/api/")) {
    event.respondWith(
      fetch(req)
        .then((res) => {
          if (res.ok) {
            const clone = res.clone();
            caches.open(API_CACHE).then((cache) => cache.put(req, clone));
          }
          return res;
        })
        .catch(() =>
          caches.match(req).then(
            (cached) =>
              cached ||
              new Response(
                JSON.stringify({ detail: "Hors ligne — requête en attente de synchronisation" }),
                { status: 503, headers: { "Content-Type": "application/json" } }
              )
          )
        )
    );
    return;
  }

  // v2.8.6 — index.html : NETWORK-FIRST (critique !)
  // Le navigateur doit TOUJOURS obtenir la dernière version d'index.html
  // car elle référence les nouveaux hashes JS/CSS après un déploiement.
  if (url.pathname === "/" || url.pathname === "/index.html") {
    event.respondWith(
      fetch(req)
        .then((res) => {
          // Mettre en cache la nouvelle version
          if (res.ok) {
            const clone = res.clone();
            caches.open(SHELL_CACHE).then((cache) => cache.put(req, clone));
          }
          return res;
        })
        .catch(() => caches.match(req))
    );
    return;
  }

  // /assets/ : CACHE-FIRST (fichiers hashés par Vite, immuables)
  // Si le fichier est en cache, il est valide (le hash ne change jamais).
  // Si pas en cache, on fetch depuis le réseau.
  if (url.pathname.startsWith("/assets/")) {
    event.respondWith(
      caches.match(req).then((cached) => {
        if (cached) return cached;
        return fetch(req).then((res) => {
          if (res.ok) {
            const clone = res.clone();
            caches.open(SHELL_CACHE).then((cache) => cache.put(req, clone));
          }
          return res;
        });
      })
    );
    return;
  }

  // Autres fichiers statiques (icons, manifest, etc.) : stale-while-revalidate
  event.respondWith(
    caches.match(req).then((cached) => {
      const fetchPromise = fetch(req)
        .then((res) => {
          if (res.ok) {
            const clone = res.clone();
            caches.open(SHELL_CACHE).then((cache) => cache.put(req, clone));
          }
          return res;
        })
        .catch(() => cached);
      return cached || fetchPromise;
    })
  );
});

// Listen for messages from the client
self.addEventListener("message", (event) => {
  if (event.data === "skipWaiting") {
    self.skipWaiting();
  }
});
