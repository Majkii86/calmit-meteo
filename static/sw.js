const CACHE_NAME = 'meteo-calmit-v1';

const CACHE_FILES = [
    '/',
    '/static/style.css',
    '/static/app.js',
    '/static/manifest.json',
    '/static/icon.png'
];

self.addEventListener('install', event => {
    event.waitUntil(
        caches.open(CACHE_NAME).then(cache => cache.addAll(CACHE_FILES))
    );
});

self.addEventListener('fetch', event => {
    event.respondWith(
        fetch(event.request).catch(() => caches.match(event.request))
    );
});