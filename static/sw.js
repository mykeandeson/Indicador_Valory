self.addEventListener("install", e => {
  console.log("Service Worker instalado");
  self.skipWaiting();
});

self.addEventListener("activate", e => {
  console.log("Service Worker ativo");
});

self.addEventListener("fetch", event => {
  event.respondWith(fetch(event.request));
});
