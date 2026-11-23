// Minimal service worker: lets the page show notifications on Android (which requires one).
// No fetch handler, so it doesn't cache anything or change how the page loads.
self.addEventListener('install', () => self.skipWaiting());
self.addEventListener('activate', e => e.waitUntil(self.clients.claim()));
self.addEventListener('notificationclick', e => {
  e.notification.close();
  e.waitUntil(self.clients.matchAll({ type: 'window', includeUncontrolled: true })
    .then(cs => cs.length ? cs[0].focus() : self.clients.openWindow('./')));
});
