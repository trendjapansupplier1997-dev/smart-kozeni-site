/* Smart Kozeni retired service worker: clear legacy caches and unregister. */
self.addEventListener('install', () => {
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  event.waitUntil((async () => {
    const keys = await caches.keys();
    await Promise.all(keys.map((key) => caches.delete(key)));
    await self.registration.unregister();
    const windows = await self.clients.matchAll({
      type: 'window',
      includeUncontrolled: true,
    });
    await Promise.allSettled(windows.map((client) => client.navigate(client.url)));
  })());
});
