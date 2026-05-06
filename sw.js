
const CACHE='smart-kozeni-v8';
const CORE=['/','/start-here/','/tiktok-lite/','/point-site/','/member/','/install/','/assets/style.css','/assets/script.js','/assets/images/icon-192.png'];
self.addEventListener('install', event=>{ event.waitUntil(caches.open(CACHE).then(cache=>cache.addAll(CORE)).then(()=>self.skipWaiting())); });
self.addEventListener('activate', event=>{ event.waitUntil(caches.keys().then(keys=>Promise.all(keys.filter(k=>k!==CACHE).map(k=>caches.delete(k)))).then(()=>self.clients.claim())); });
self.addEventListener('fetch', event=>{
  const req=event.request;
  if(req.method!=='GET') return;
  event.respondWith(fetch(req).then(res=>{ const copy=res.clone(); if(new URL(req.url).origin===location.origin){ caches.open(CACHE).then(cache=>cache.put(req,copy)); } return res; }).catch(()=>caches.match(req).then(cached=>cached||caches.match('/'))));
});
