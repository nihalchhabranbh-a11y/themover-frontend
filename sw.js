const CACHE_NAME = 'themover-v8';
const OFFLINE_URLS = [
  '/',
  '/index.html',
  '/manifest.json',
  '/TheMover-Mac.zip',
  '/TheMover-PC.zip',
  'https://cdn.tailwindcss.com?plugins=forms,container-queries',
  'https://cdn.socket.io/4.7.5/socket.io.min.js',
  'https://cdnjs.cloudflare.com/ajax/libs/qrcodejs/1.0.0/qrcode.min.js',
  'https://unpkg.com/html5-qrcode',
  'https://cdnjs.cloudflare.com/ajax/libs/lz-string/1.5.0/lz-string.min.js'
];

self.addEventListener('install', (event) => {
  self.skipWaiting();
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      // Don't fail install if a CDN fails
      return Promise.all(
        OFFLINE_URLS.map(url => {
          return cache.add(url).catch(err => console.log('Failed to cache:', url));
        })
      );
    })
  );
});

self.addEventListener('activate', (event) => {
  event.waitUntil(self.clients.claim());
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((cacheName) => {
          if (cacheName !== CACHE_NAME) {
            return caches.delete(cacheName);
          }
        })
      );
    })
  );
});

self.addEventListener('fetch', (event) => {
  // Intercept Android Native Share Target POST requests
  if (event.request.method === 'POST' && event.request.url.includes('/index.html')) {
    event.respondWith((async () => {
      try {
        const formData = await event.request.formData();
        const file = formData.get('shared_file');
        if (file) {
          const apiFormData = new FormData();
          apiFormData.append('file', file);
          await fetch('https://themover-3r8d.onrender.com/api/upload', {
            method: 'POST',
            body: apiFormData
          });
        }
        return Response.redirect('/index.html?upload_success=true', 303);
      } catch (error) {
        return Response.redirect('/index.html?upload_error=true', 303);
      }
    })());
    return;
  }

  // API calls should never be cached
  if (event.request.url.includes('/api/')) {
    event.respondWith(fetch(event.request));
    return;
  }

  // Cache-First strategy for static assets, Network-First for HTML
  event.respondWith(
    caches.match(event.request).then((cachedResponse) => {
      if (cachedResponse) return cachedResponse;
      return fetch(event.request).then((networkResponse) => {
        // Cache the dynamically fetched assets if they are GET requests
        if (event.request.method === 'GET' && !event.request.url.includes('/socket.io/')) {
          const responseToCache = networkResponse.clone();
          caches.open(CACHE_NAME).then((cache) => {
            cache.put(event.request, responseToCache);
          });
        }
        return networkResponse;
      }).catch(() => {
        // If network fails (Offline mode), try to serve index.html for navigation requests
        if (event.request.mode === 'navigate') {
          return caches.match('/index.html');
        }
      });
    })
  );
});
