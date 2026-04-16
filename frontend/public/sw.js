// Enhanced Service Worker for Tech News Agent PWA
// Provides intelligent caching, offline functionality, and background sync
// Requirements: 12.7, 8.6, 8.7, 8.8

// Detect development mode
const IS_DEVELOPMENT =
  self.location.hostname === 'localhost' || self.location.hostname === '127.0.0.1';

const CACHE_VERSION = '2.0.0';
const CACHE_NAME = `tech-news-agent-v${CACHE_VERSION}`;
const STATIC_CACHE_NAME = `tech-news-static-v${CACHE_VERSION}`;
const DYNAMIC_CACHE_NAME = `tech-news-dynamic-v${CACHE_VERSION}`;
const API_CACHE_NAME = `tech-news-api-v${CACHE_VERSION}`;
const IMAGE_CACHE_NAME = `tech-news-images-v${CACHE_VERSION}`;

// Static assets to cache immediately (only include files that exist)
const STATIC_ASSETS = [
  '/',
  '/offline.html',
  '/manifest.json',
  // Note: Next.js static assets are cached dynamically on first request
  // Don't include /_next/static paths here as they may not exist at install time
];

// Skip service worker caching in development mode
if (IS_DEVELOPMENT) {
  console.log('[SW] Running in DEVELOPMENT mode - caching disabled for faster iteration');
}

// API endpoints to cache with different strategies
const API_CACHE_STRATEGIES = {
  // Long-term cache for AI analysis
  longTerm: ['/api/analysis/', '/api/articles/'],
  // Medium-term cache for user data
  mediumTerm: ['/api/reading-list', '/api/recommendations', '/api/subscriptions'],
  // Short-term cache for dynamic data
  shortTerm: ['/api/system/status', '/api/notifications'],
};

// Maximum cache sizes (increased for better performance)
const MAX_CACHE_SIZE = {
  static: 100,
  dynamic: 200,
  api: 500,
  images: 300,
};

// Enhanced cache duration in milliseconds
const CACHE_DURATION = {
  static: 30 * 24 * 60 * 60 * 1000, // 30 days
  dynamic: 7 * 24 * 60 * 60 * 1000, // 7 days
  apiLongTerm: 24 * 60 * 60 * 1000, // 24 hours (AI analysis)
  apiMediumTerm: 30 * 60 * 1000, // 30 minutes (user data)
  apiShortTerm: 5 * 60 * 1000, // 5 minutes (system status)
  images: 7 * 24 * 60 * 60 * 1000, // 7 days
};

// Install event - cache static assets
self.addEventListener('install', (event) => {
  console.log('[SW] Installing service worker...');

  event.waitUntil(
    Promise.all([
      caches.open(STATIC_CACHE_NAME).then((cache) => {
        console.log('[SW] Caching static assets');
        // Use addAll with error handling to prevent installation failure
        return cache.addAll(STATIC_ASSETS).catch((error) => {
          console.error('[SW] Failed to cache some static assets:', error);
          // Continue installation even if some assets fail to cache
          return Promise.resolve();
        });
      }),
      // Skip waiting to activate immediately
      self.skipWaiting(),
    ])
  );
});

// Activate event - clean up old caches
self.addEventListener('activate', (event) => {
  console.log('[SW] Activating service worker...');

  event.waitUntil(
    Promise.all([
      // Clean up old caches
      caches.keys().then((cacheNames) => {
        return Promise.all(
          cacheNames.map((cacheName) => {
            if (
              cacheName !== STATIC_CACHE_NAME &&
              cacheName !== DYNAMIC_CACHE_NAME &&
              cacheName !== API_CACHE_NAME
            ) {
              console.log('[SW] Deleting old cache:', cacheName);
              return caches.delete(cacheName);
            }
          })
        );
      }),
      // Take control of all clients
      self.clients.claim(),
    ])
  );
});

// Fetch event - handle network requests with intelligent caching
self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);

  // Skip non-GET requests
  if (request.method !== 'GET') {
    return;
  }

  // Skip chrome-extension and other non-http requests
  if (!url.protocol.startsWith('http')) {
    return;
  }

  // In development mode, bypass service worker for most requests
  if (IS_DEVELOPMENT) {
    // Only handle offline page and manifest in development
    if (url.pathname === '/offline.html' || url.pathname === '/manifest.json') {
      event.respondWith(fetch(request));
    }
    return;
  }

  // Handle different types of requests with appropriate strategies (production only)
  if (url.pathname.startsWith('/api/')) {
    // API requests - intelligent caching based on endpoint
    event.respondWith(handleApiRequest(request));
  } else if (url.pathname.match(/\.(jpg|jpeg|png|gif|webp|avif|svg|ico)$/)) {
    // Image requests - cache first with long expiration
    event.respondWith(handleImageRequest(request));
  } else if (url.pathname.startsWith('/_next/static/')) {
    // Static assets - cache first with long expiration
    event.respondWith(handleStaticAssetRequest(request));
  } else if (
    STATIC_ASSETS.some((asset) => url.pathname === asset || url.pathname.startsWith(asset))
  ) {
    // Static pages - stale while revalidate
    event.respondWith(handleStaticPageRequest(request));
  } else {
    // Dynamic content - network first with cache fallback
    event.respondWith(handleDynamicRequest(request));
  }
});

// Handle API requests with intelligent caching based on endpoint type
async function handleApiRequest(request) {
  const url = new URL(request.url);
  const cache = await caches.open(API_CACHE_NAME);

  // Determine cache strategy based on endpoint
  let cacheStrategy = 'shortTerm';
  let cacheDuration = CACHE_DURATION.apiShortTerm;

  if (API_CACHE_STRATEGIES.longTerm.some((pattern) => url.pathname.includes(pattern))) {
    cacheStrategy = 'longTerm';
    cacheDuration = CACHE_DURATION.apiLongTerm;
  } else if (API_CACHE_STRATEGIES.mediumTerm.some((pattern) => url.pathname.includes(pattern))) {
    cacheStrategy = 'mediumTerm';
    cacheDuration = CACHE_DURATION.apiMediumTerm;
  }

  try {
    // Try network first for fresh data
    const networkResponse = await fetch(request);

    if (networkResponse.ok) {
      // Cache successful responses with appropriate headers
      const responseClone = networkResponse.clone();
      const responseWithHeaders = new Response(responseClone.body, {
        status: responseClone.status,
        statusText: responseClone.statusText,
        headers: {
          ...Object.fromEntries(responseClone.headers.entries()),
          'sw-cache-strategy': cacheStrategy,
          'sw-cached-at': new Date().toISOString(),
        },
      });

      await cache.put(request, responseWithHeaders);
      await limitCacheSize(API_CACHE_NAME, MAX_CACHE_SIZE.api);
    }

    return networkResponse;
  } catch (error) {
    console.log('[SW] Network failed for API request, trying cache:', request.url);

    // Fallback to cache
    const cachedResponse = await cache.match(request);
    if (cachedResponse) {
      // Check if cached response is still fresh
      const cachedAt = cachedResponse.headers.get('sw-cached-at');
      if (cachedAt) {
        const cacheAge = Date.now() - new Date(cachedAt).getTime();
        if (cacheAge < cacheDuration) {
          // Add header to indicate cached response
          const response = cachedResponse.clone();
          response.headers.set('sw-cache-hit', 'true');
          return response;
        }
      }
    }

    // Return offline response for failed API requests
    return new Response(
      JSON.stringify({
        error: 'Offline',
        message: 'This content is not available offline',
        cached: false,
      }),
      {
        status: 503,
        statusText: 'Service Unavailable',
        headers: {
          'Content-Type': 'application/json',
          'sw-offline': 'true',
        },
      }
    );
  }
}

// Handle image requests with cache-first strategy
async function handleImageRequest(request) {
  const cache = await caches.open(IMAGE_CACHE_NAME);

  // Try cache first for images
  const cachedResponse = await cache.match(request);
  if (cachedResponse) {
    return cachedResponse;
  }

  try {
    // Fallback to network
    const networkResponse = await fetch(request);

    if (networkResponse.ok) {
      // Cache images with optimization headers
      const responseClone = networkResponse.clone();
      await cache.put(request, responseClone);
      await limitCacheSize(IMAGE_CACHE_NAME, MAX_CACHE_SIZE.images);
    }

    return networkResponse;
  } catch (error) {
    console.log('[SW] Failed to fetch image:', request.url);

    // Return placeholder image for failed image requests
    return new Response(
      '<svg width="200" height="200" xmlns="http://www.w3.org/2000/svg"><rect width="200" height="200" fill="#f3f4f6"/><text x="100" y="100" text-anchor="middle" fill="#9ca3af">Image unavailable</text></svg>',
      {
        headers: {
          'Content-Type': 'image/svg+xml',
          'sw-placeholder': 'true',
        },
      }
    );
  }
}

// Handle static assets with cache-first strategy
async function handleStaticAssetRequest(request) {
  // In development, always use network first to avoid stale cache issues
  if (self.location.hostname === 'localhost' || self.location.hostname === '127.0.0.1') {
    try {
      const networkResponse = await fetch(request);
      return networkResponse;
    } catch (error) {
      console.log('[SW] Network failed for static asset in dev mode:', request.url);
      // Don't throw - just return a simple error response
      return new Response('Development server unavailable', {
        status: 503,
        statusText: 'Service Unavailable',
      });
    }
  }

  const cache = await caches.open(STATIC_CACHE_NAME);

  // Try cache first for static assets (production only)
  const cachedResponse = await cache.match(request);
  if (cachedResponse) {
    return cachedResponse;
  }

  try {
    // Fallback to network
    const networkResponse = await fetch(request);

    if (networkResponse.ok) {
      // Cache static assets with long expiration
      const responseClone = networkResponse.clone();
      await cache.put(request, responseClone);
      await limitCacheSize(STATIC_CACHE_NAME, MAX_CACHE_SIZE.static);
    }

    return networkResponse;
  } catch (error) {
    console.log('[SW] Failed to fetch static asset:', request.url);
    return new Response('Asset unavailable', {
      status: 503,
      statusText: 'Service Unavailable',
    });
  }
}

// Handle static pages with stale-while-revalidate strategy
async function handleStaticPageRequest(request) {
  const cache = await caches.open(STATIC_CACHE_NAME);

  // Get cached version immediately
  const cachedResponse = await cache.match(request);

  // Start network request in background
  const networkResponsePromise = fetch(request)
    .then(async (networkResponse) => {
      if (networkResponse.ok) {
        const responseClone = networkResponse.clone();
        await cache.put(request, responseClone);
        await limitCacheSize(STATIC_CACHE_NAME, MAX_CACHE_SIZE.static);
      }
      return networkResponse;
    })
    .catch(() => null);

  // Return cached version immediately if available
  if (cachedResponse) {
    // Update cache in background
    networkResponsePromise.catch(() => {
      console.log('[SW] Background update failed for:', request.url);
    });

    return cachedResponse;
  }

  // If no cache, wait for network
  try {
    return await networkResponsePromise;
  } catch (error) {
    // Return offline page for navigation requests
    if (request.mode === 'navigate') {
      const offlineResponse = await cache.match('/offline.html');
      if (offlineResponse) {
        return offlineResponse;
      }
    }
    throw error;
  }
}

// Handle dynamic requests with network-first strategy
async function handleDynamicRequest(request) {
  const cache = await caches.open(DYNAMIC_CACHE_NAME);

  try {
    // Try network first
    const networkResponse = await fetch(request);

    if (networkResponse.ok) {
      // Cache successful responses
      const responseClone = networkResponse.clone();
      await cache.put(request, responseClone);

      // Clean up old cache entries
      await limitCacheSize(DYNAMIC_CACHE_NAME, MAX_CACHE_SIZE.dynamic);
    }

    return networkResponse;
  } catch (error) {
    console.log('[SW] Network failed for dynamic request, trying cache:', request.url);

    // Fallback to cache
    const cachedResponse = await cache.match(request);
    if (cachedResponse) {
      return cachedResponse;
    }

    // Return offline page for navigation requests
    if (request.mode === 'navigate') {
      const offlineResponse = await caches
        .open(STATIC_CACHE_NAME)
        .then((cache) => cache.match('/offline.html'));
      if (offlineResponse) {
        return offlineResponse;
      }
    }

    throw error;
  }
}

// Limit cache size by removing oldest entries
async function limitCacheSize(cacheName, maxSize) {
  const cache = await caches.open(cacheName);
  const keys = await cache.keys();

  if (keys.length > maxSize) {
    const keysToDelete = keys.slice(0, keys.length - maxSize);
    await Promise.all(keysToDelete.map((key) => cache.delete(key)));
    console.log(`[SW] Cleaned up ${keysToDelete.length} entries from ${cacheName}`);
  }
}

// Background sync for offline actions
self.addEventListener('sync', (event) => {
  console.log('[SW] Background sync triggered:', event.tag);

  if (event.tag === 'background-sync-articles') {
    event.waitUntil(syncOfflineActions());
  }
});

// Sync offline actions when connection is restored
async function syncOfflineActions() {
  try {
    // Get offline actions from IndexedDB or localStorage
    const offlineActions = await getOfflineActions();

    for (const action of offlineActions) {
      try {
        await fetch(action.url, {
          method: action.method,
          headers: action.headers,
          body: action.body,
        });

        // Remove successful action
        await removeOfflineAction(action.id);
        console.log('[SW] Synced offline action:', action.id);
      } catch (error) {
        console.log('[SW] Failed to sync offline action:', action.id, error);
      }
    }
  } catch (error) {
    console.log('[SW] Background sync failed:', error);
  }
}

// Placeholder functions for offline action management
// These would typically use IndexedDB for persistent storage
async function getOfflineActions() {
  // Implementation would retrieve actions from IndexedDB
  return [];
}

async function removeOfflineAction(actionId) {
  // Implementation would remove action from IndexedDB
  console.log('[SW] Removing offline action:', actionId);
}

// Handle push notifications (if implemented)
self.addEventListener('push', (event) => {
  console.log('[SW] Push notification received');

  if (event.data) {
    const data = event.data.json();

    event.waitUntil(
      self.registration.showNotification(data.title, {
        body: data.body,
        icon: '/icons/icon-192x192.png',
        badge: '/icons/badge-72x72.png',
        tag: data.tag || 'default',
        data: data.data,
        actions: data.actions || [],
      })
    );
  }
});

// Handle notification clicks
self.addEventListener('notificationclick', (event) => {
  console.log('[SW] Notification clicked:', event.notification.tag);

  event.notification.close();

  const urlToOpen = event.notification.data?.url || '/';

  event.waitUntil(
    self.clients.matchAll({ type: 'window' }).then((clients) => {
      // Check if there's already a window/tab open with the target URL
      for (const client of clients) {
        if (client.url === urlToOpen && 'focus' in client) {
          return client.focus();
        }
      }

      // If not, open a new window/tab
      if (self.clients.openWindow) {
        return self.clients.openWindow(urlToOpen);
      }
    })
  );
});

// Log service worker errors
self.addEventListener('error', (event) => {
  console.error('[SW] Service worker error:', event.error);
});

self.addEventListener('unhandledrejection', (event) => {
  console.error('[SW] Unhandled promise rejection:', event.reason);
});
