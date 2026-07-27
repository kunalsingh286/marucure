const CACHE_NAME = 'marucure-offline-v5';

// All the files and external CDNs required for the app to function offline
const URLS_TO_CACHE = [
    // --- Vercel Clean URLs (What the browser actually requests) ---
    '/',
    '/about',
    '/solutions',
    '/app',
    '/app/',

    // --- Marketing Website ---
    '/index.html',
    '/about.html',
    '/solutions.html',
    '/style.css',
    '/script.js',
    '/assets/hero.png',
    '/assets/images/hero_edge_ai.png',
    '/assets/images/solution_xray.png',
    '/assets/images/solution_spiro.png',

    // --- Clinical App (PWA Node) ---
    '/app/index.html',
    '/app/app.js?v=5',
    '/app/dashboard.css',
    '/assets/models/model_fir.tflite',
    '/assets/models/model_silicosis.tflite',

    // TensorFlow.js Libraries
    'https://cdn.jsdelivr.net/npm/@tensorflow/tfjs/dist/tf.min.js',
    'https://cdn.jsdelivr.net/npm/@tensorflow/tfjs-tflite@0.0.1-alpha.9/dist/tf-tflite.min.js',
    
    // DICOM Parser
    'https://unpkg.com/daikon@1.2.43/release/daikon-min.js',
    
    // IndexedDB Wrapper
    'https://cdn.jsdelivr.net/npm/idb@7/build/umd.js',

    // Google Fonts & Material Icons
    'https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=Outfit:wght@600;800&display=swap',
    'https://fonts.googleapis.com/icon?family=Material+Icons'
];

// 1. Install Event: Download all required files into the cache
self.addEventListener('install', event => {
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then(cache => {
                console.log('[Service Worker] Caching all offline dependencies...');
                // We use a safe caching strategy so one failure doesn't break the whole install
                return Promise.allSettled(
                    URLS_TO_CACHE.map(url => {
                        return fetch(new Request(url, { mode: 'no-cors' })).then(response => {
                            if (response.ok || response.type === 'opaque') {
                                return cache.put(url, response);
                            }
                        });
                    })
                );
            })
    );
    self.skipWaiting();
});

// 2. Activate Event: Clean up old caches
self.addEventListener('activate', event => {
    event.waitUntil(
        caches.keys().then(cacheNames => {
            return Promise.all(
                cacheNames.map(cacheName => {
                    if (cacheName !== CACHE_NAME) {
                        return caches.delete(cacheName);
                    }
                })
            );
        })
    );
    self.clients.claim();
});

// 3. Fetch Event: Serve from cache first, fallback to network
self.addEventListener('fetch', event => {
    // Only intercept GET requests
    if (event.request.method !== 'GET') return;
    
    event.respondWith(
        caches.match(event.request, { ignoreSearch: true }).then(response => {
            // Return cached response if found
            if (response) {
                return response;
            }
            
            // Otherwise try to fetch from network
            return fetch(event.request).then(networkResponse => {
                // Dynamically cache ALL successful network responses (like Google Fonts .woff2 files)
                if (networkResponse && networkResponse.status === 200 && networkResponse.type !== 'error') {
                    const responseToCache = networkResponse.clone();
                    caches.open(CACHE_NAME).then(cache => {
                        cache.put(event.request, responseToCache);
                    });
                }
                return networkResponse;
            }).catch(err => {
                console.warn('[Service Worker] Network request failed and no cache found:', event.request.url);
            });
        })
    );
});
