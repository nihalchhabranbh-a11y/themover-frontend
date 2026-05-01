const CACHE_NAME = 'themover-v11';
const STATIC_ASSETS = [
  '/manifest.json',
  '/TheMover-Mac.zip',
  '/TheMover-PC.zip',
];

self.addEventListener('install', (event) => {
  self.skipWaiting();
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return Promise.all(
        STATIC_ASSETS.map(url => cache.add(url).catch(() => {}))
      );
    })
  );
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    Promise.all([
      self.clients.claim(),
      caches.keys().then(keys =>
        Promise.all(keys.filter(k => k !== CACHE_NAME).map(k => caches.delete(k)))
      )
    ])
  );
});

self.addEventListener('fetch', (event) => {
  const url = event.request.url;

  // Handle Android Share Target
  if (event.request.method === 'POST' && url.includes('/index.html')) {
    event.respondWith((async () => {
      try {
        const formData = await event.request.formData();
        const file = formData.get('shared_file');
        if (file) {
          const apiFormData = new FormData();
          apiFormData.append('file', file);
          await fetch('https://themover-3r8d.onrender.com/api/upload', {
            method: 'POST', body: apiFormData
          });
        }
        return Response.redirect('/index.html?upload_success=true', 303);
      } catch {
        return Response.redirect('/index.html?upload_error=true', 303);
      }
    })());
    return;
  }

  // Never cache API or socket calls
  if (url.includes('/api/') || url.includes('/socket.io/')) {
    event.respondWith(fetch(event.request));
    return;
  }

  // HTML pages: Network-First (always get latest version)
  if (event.request.mode === 'navigate' || url.endsWith('.html')) {
    event.respondWith(
      fetch(event.request).catch(() => caches.match('/index.html'))
    );
    return;
  }

  // Static zips / manifest: Cache-First
  event.respondWith(
    caches.match(event.request).then(cached => {
      if (cached) return cached;
      return fetch(event.request).then(res => {
        if (event.request.method === 'GET') {
          const clone = res.clone();
          caches.open(CACHE_NAME).then(c => c.put(event.request, clone));
        }
        return res;
      });
    })
  );
});
