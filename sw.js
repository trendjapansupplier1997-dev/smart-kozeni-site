// v28: retire old caches during rapid site structure updates.
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
  })());
});
self.addEventListener('fetch', event => { return; });
