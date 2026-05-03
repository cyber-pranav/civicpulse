/** @module ServiceWorker */
var CACHE_NAME = 'civicpulse-v1';
var STATIC_ASSETS = ['/', '/index.html', '/app.js', '/constants.js', '/utils.js', '/modules.js', '/manifest.json'];
var API_PATTERNS = ['/api/', 'generativelanguage.googleapis.com', 'translation.googleapis.com', 'firestore.googleapis.com', 'language.googleapis.com'];

function isAPI(url) { return API_PATTERNS.some(function(p) { return url.includes(p); }); }

self.addEventListener('install', function(e) {
  e.waitUntil(caches.open(CACHE_NAME).then(function(c) { return c.addAll(STATIC_ASSETS); }));
  self.skipWaiting();
});

self.addEventListener('activate', function(e) {
  e.waitUntil(caches.keys().then(function(names) {
    return Promise.all(names.filter(function(n) { return n !== CACHE_NAME; }).map(function(n) { return caches.delete(n); }));
  }));
  self.clients.claim();
});

self.addEventListener('fetch', function(e) {
  if (e.request.method !== 'GET') return;
  if (isAPI(e.request.url)) {
    e.respondWith(fetch(e.request).catch(function() { return caches.match(e.request); }));
  } else {
    e.respondWith(caches.match(e.request).then(function(c) {
      if (c) return c;
      return fetch(e.request).then(function(r) {
        if (r && r.status === 200) { var rc = r.clone(); caches.open(CACHE_NAME).then(function(ca) { ca.put(e.request, rc); }); }
        return r;
      });
    }));
  }
});
