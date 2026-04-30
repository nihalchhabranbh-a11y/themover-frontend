self.addEventListener('install', (event) => {
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  event.waitUntil(self.clients.claim());
});

self.addEventListener('fetch', (event) => {
  // Intercept Android Native Share Target POST requests
  if (event.request.method === 'POST' && event.request.url.includes('/index.html')) {
    event.respondWith((async () => {
      try {
        const formData = await event.request.formData();
        const file = formData.get('shared_file');
        
        if (file) {
          // Send it straight to the Render API from the background
          const apiFormData = new FormData();
          apiFormData.append('file', file);
          
          await fetch('https://themover-3r8d.onrender.com/api/upload', {
            method: 'POST',
            body: apiFormData
          });
        }
        
        // Redirect to homepage showing success
        return Response.redirect('/index.html?upload_success=true', 303);
      } catch (error) {
        console.error('Share Target Error:', error);
        return Response.redirect('/index.html?upload_error=true', 303);
      }
    })());
    return;
  }

  // Normal pass-through for everything else
  event.respondWith(fetch(event.request));
});
