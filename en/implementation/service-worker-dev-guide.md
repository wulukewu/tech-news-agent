# Service Worker Development Guide

## Problem: Service Worker Causing Reload Loops

When developing with hot module replacement (HMR), service workers can cause issues:

- Infinite reload loops when dev server restarts
- Stale cached assets
- Failed fetch errors
- Difficulty debugging

## Solution 1: Disable Service Worker in Development (Recommended)

The service worker has been updated to automatically bypass caching in development mode (localhost).

### Verify It's Working

1. Open DevTools Console
2. Look for: `[SW] Running in DEVELOPMENT mode - caching disabled for faster iteration`
3. Service worker should not intercept requests

### If Still Having Issues

**Unregister the service worker:**

1. Open Chrome DevTools (F12)
2. Go to **Application** tab
3. Click **Service Workers** in left sidebar
4. Click **Unregister** next to any registered workers
5. Refresh the page (Ctrl+Shift+R)

## Solution 2: Conditional Registration

Update the service worker registration to only run in production:

**File:** `frontend/components/PerformanceInitializer.tsx`

```typescript
export function ServiceWorkerRegistration() {
  useEffect(() => {
    // Only register service worker in production
    if (process.env.NODE_ENV !== 'production') {
      console.log('⚠️ Service Worker disabled in development');
      return;
    }

    if (typeof window === 'undefined') return;

    const registerServiceWorker = async () => {
      if ('serviceWorker' in navigator) {
        try {
          const registration = await navigator.serviceWorker.register('/sw.js', {
            scope: '/',
          });
          console.log('✅ Service Worker registered successfully');
        } catch (error) {
          console.error('Service Worker registration failed:', error);
        }
      }
    };

    if (document.readyState === 'complete') {
      registerServiceWorker();
    } else {
      window.addEventListener('load', registerServiceWorker);
    }
  }, []);

  return null;
}
```

## Solution 3: Manual Unregister Script

Create a script to quickly unregister service workers:

**File:** `frontend/public/unregister-sw.html`

```html
<!DOCTYPE html>
<html>
  <head>
    <title>Unregister Service Worker</title>
  </head>
  <body>
    <h1>Service Worker Unregistration</h1>
    <div id="status">Checking...</div>
    <script>
      async function unregisterServiceWorkers() {
        const statusDiv = document.getElementById('status');

        if ('serviceWorker' in navigator) {
          const registrations = await navigator.serviceWorker.getRegistrations();

          if (registrations.length === 0) {
            statusDiv.innerHTML = '<p style="color: green;">✅ No service workers registered</p>';
            return;
          }

          for (const registration of registrations) {
            await registration.unregister();
            console.log('Unregistered:', registration.scope);
          }

          statusDiv.innerHTML = `
          <p style="color: green;">✅ Unregistered ${registrations.length} service worker(s)</p>
          <p>Please refresh the page to complete the process.</p>
          <button onclick="window.location.reload()">Refresh Now</button>
        `;
        } else {
          statusDiv.innerHTML = '<p style="color: orange;">⚠️ Service workers not supported</p>';
        }
      }

      unregisterServiceWorkers();
    </script>
  </body>
</html>
```

**Usage:** Navigate to `http://localhost:3000/unregister-sw.html`

## Current Service Worker Behavior

The service worker now:

✅ **Development Mode (localhost):**

- Bypasses all caching
- Only handles offline.html and manifest.json
- Allows HMR to work normally
- No reload loops

✅ **Production Mode:**

- Full caching enabled
- Offline functionality active
- Background sync enabled
- PWA features work

## Debugging Service Worker Issues

### Check Registration Status

```javascript
// In browser console
navigator.serviceWorker.getRegistrations().then((registrations) => {
  console.log('Registered service workers:', registrations.length);
  registrations.forEach((reg) => console.log('Scope:', reg.scope));
});
```

### Check Cache Status

```javascript
// In browser console
caches.keys().then((keys) => {
  console.log('Cache names:', keys);
  keys.forEach((key) => {
    caches.open(key).then((cache) => {
      cache.keys().then((requests) => {
        console.log(`${key}: ${requests.length} items`);
      });
    });
  });
});
```

### Clear All Caches

```javascript
// In browser console
caches
  .keys()
  .then((keys) => {
    return Promise.all(keys.map((key) => caches.delete(key)));
  })
  .then(() => {
    console.log('All caches cleared');
    location.reload();
  });
```

## Best Practices

### During Development

1. **Disable service worker** or use development mode bypass
2. **Clear cache regularly** when testing PWA features
3. **Use incognito mode** for clean testing
4. **Check DevTools Application tab** for service worker status

### Before Production

1. **Test service worker** in production build locally
2. **Verify offline functionality** works
3. **Test cache strategies** are appropriate
4. **Check update mechanism** works correctly

## Common Issues

### Issue: Infinite Reload Loop

**Symptoms:**

- Page keeps reloading
- Console shows "Failed to fetch" errors
- Dev server logs show repeated requests

**Solution:**

1. Unregister service worker
2. Clear all caches
3. Hard refresh (Ctrl+Shift+R)
4. Verify development mode bypass is active

### Issue: Stale Assets

**Symptoms:**

- Changes not appearing
- Old code running
- CSS not updating

**Solution:**

1. Clear service worker caches
2. Unregister service worker
3. Hard refresh
4. Check cache version in sw.js

### Issue: Service Worker Won't Update

**Symptoms:**

- New service worker stuck in "waiting"
- Old version still active

**Solution:**

1. Close all tabs with the site
2. Unregister old service worker
3. Refresh to register new one
4. Or use `skipWaiting()` in sw.js

## Quick Commands

```bash
# Clear all browser data (Chrome)
# DevTools → Application → Clear storage → Clear site data

# Unregister service workers (Console)
navigator.serviceWorker.getRegistrations().then(r => r.forEach(reg => reg.unregister()))

# Clear all caches (Console)
caches.keys().then(k => Promise.all(k.map(key => caches.delete(key))))

# Hard refresh
# Ctrl+Shift+R (Windows/Linux)
# Cmd+Shift+R (Mac)
```

## Additional Resources

- [Service Worker API - MDN](https://developer.mozilla.org/en-US/docs/Web/API/Service_Worker_API)
- [Workbox - Google](https://developers.google.com/web/tools/workbox)
- [PWA Best Practices](https://web.dev/pwa/)

---

**Note:** The service worker has been configured to automatically detect development mode and bypass caching. You should not experience reload loops anymore. If issues persist, manually unregister the service worker using the steps above.
