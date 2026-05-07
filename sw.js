// v22: hard retire old PWA/service-worker caches during rapid design updates.
self.addEventListener('install', event => {
  self.skipWaiting();
});

self.addEventListener('activate', event => {
  event.waitUntil((async () => {
    try {
      const keys = await caches.keys();
      await Promise.all(keys.map(key => caches.delete(key)));
    } catch (e) {}
    try { await self.registration.unregister(); } catch (e) {}
    try {
      const clients = await self.clients.matchAll({ type: 'window', includeUncontrolled: true });
      for (const client of clients) {
        const url = new URL(client.url);
        if (!url.searchParams.has('kozeni_sw_reset')) {
          url.searchParams.set('kozeni_sw_reset', 'v22');
          client.navigate(url.toString());
        }
      }
    } catch (e) {}
  })());
});

self.addEventListener('fetch', event => {
  return;
});
