# Frontend Errors Fix Guide

## Issues Identified

Based on the console errors, there are several critical issues affecting your frontend:

### 1. Content Security Policy (CSP) Violation

**Error:** `Connecting to 'http://localhost:8000/api/auth/me' violates CSP directive: "connect-src 'self' https:"`

**Root Cause:** The CSP policy in `next.config.js` only allows HTTPS connections, but your API is running on HTTP localhost.

**Impact:** Authentication and all API calls are blocked.

### 2. Missing Static Assets

**Errors:**

- All PWA icons (144x144, 192x192, 512x512, etc.) - 404
- Font files (inter-var.woff2, inter-var-italic.woff2) - 404
- Logo image (logo.svg) - 404
- Shortcut icons for PWA - 404

**Root Cause:** The `frontend/public/icons/` directory only contains `.gitkeep` - no actual icon files exist.

**Impact:**

- PWA installation fails
- Poor visual appearance
- Multiple resource loading errors
- Service Worker cache failures

### 3. Service Worker Cache Failures

**Error:** `TypeError: Failed to execute 'addAll' on 'Cache': Request failed`

**Root Cause:** Service Worker tries to cache missing assets (icons, fonts, images).

**Impact:** PWA offline functionality broken.

### 4. Performance Budget Violations

**Warning:** `JavaScript: 2898KB (budget: 500KB)`

**Root Cause:** Large bundle size, possibly from:

- Unoptimized imports
- Large dependencies
- Missing code splitting

**Impact:** Slow initial page load, poor performance metrics.

---

## Solutions

### Fix 1: Update CSP to Allow Localhost API

**File:** `frontend/next.config.js`

**Change the CSP header to allow HTTP localhost in development:**

```javascript
{
  key: 'Content-Security-Policy',
  value: process.env.NODE_ENV === 'development'
    ? "default-src 'self'; script-src 'self' 'unsafe-eval' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self' data:; connect-src 'self' http://localhost:* https:; manifest-src 'self';"
    : "default-src 'self'; script-src 'self' 'unsafe-eval' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self' data:; connect-src 'self' https:; manifest-src 'self';",
},
```

**Key change:** Added `http://localhost:*` to `connect-src` in development mode.

---

### Fix 2: Generate Missing PWA Icons

You need to create PWA icons. Here are your options:

#### Option A: Use an Icon Generator Tool

1. Create a base icon (512x512 PNG)
2. Use a PWA icon generator:
   - https://www.pwabuilder.com/imageGenerator
   - https://realfavicongenerator.net/

#### Option B: Use a Placeholder Script

Create `frontend/scripts/generate-icons.js`:

```javascript
const sharp = require('sharp');
const fs = require('fs');
const path = require('path');

const sizes = [72, 96, 128, 144, 152, 192, 384, 512];
const iconsDir = path.join(__dirname, '../public/icons');

// Create a simple placeholder icon
async function generateIcons() {
  if (!fs.existsSync(iconsDir)) {
    fs.mkdirSync(iconsDir, { recursive: true });
  }

  // Create base SVG
  const svg = `
    <svg width="512" height="512" xmlns="http://www.w3.org/2000/svg">
      <rect width="512" height="512" fill="#0f172a"/>
      <text x="50%" y="50%" font-size="200" fill="#ffffff"
            text-anchor="middle" dominant-baseline="middle"
            font-family="Arial, sans-serif" font-weight="bold">TN</text>
    </svg>
  `;

  for (const size of sizes) {
    await sharp(Buffer.from(svg))
      .resize(size, size)
      .png()
      .toFile(path.join(iconsDir, `icon-${size}x${size}.png`));

    console.log(`✓ Generated icon-${size}x${size}.png`);
  }

  console.log('✓ All icons generated successfully!');
}

generateIcons().catch(console.error);
```

**Install sharp:** `npm install --save-dev sharp`

**Run:** `node frontend/scripts/generate-icons.js`

---

### Fix 3: Fix Font Loading Issues

The app is trying to load Inter font variants that don't exist.

**File:** Check where fonts are referenced (likely in `app/layout.tsx` or `globals.css`)

**Option A: Use Next.js Font Optimization**

```typescript
// app/layout.tsx
import { Inter } from 'next/font/google'

const inter = Inter({
  subsets: ['latin'],
  display: 'swap',
  variable: '--font-inter'
})

export default function RootLayout({ children }) {
  return (
    <html lang="en" className={inter.variable}>
      <body>{children}</body>
    </html>
  )
}
```

**Option B: Remove Font Preloading**

Find and remove these lines from your HTML head or PerformanceInitializer:

```html
<link rel="preload" href="/fonts/inter-var.woff2" as="font" />
<link rel="preload" href="/fonts/inter-var-italic.woff2" as="font" />
```

---

### Fix 4: Fix Service Worker Cache List

**File:** `frontend/public/sw.js`

Update the cache list to only include files that actually exist:

```javascript
const CACHE_NAME = 'tech-news-v1';
const urlsToCache = [
  '/',
  '/offline.html',
  // Remove references to missing assets
  // Only cache files that exist
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      // Use addAll with error handling
      return cache.addAll(urlsToCache).catch((err) => {
        console.error('[SW] Cache addAll failed:', err);
        // Continue installation even if caching fails
        return Promise.resolve();
      });
    })
  );
});
```

---

### Fix 5: Reduce Bundle Size

**Immediate fixes:**

1. **Check PerformanceInitializer component** - it might be importing too much:

```typescript
// Use dynamic imports for heavy components
const HeavyComponent = dynamic(() => import('./HeavyComponent'), {
  loading: () => <div>Loading...</div>,
  ssr: false
});
```

2. **Analyze bundle:**

```bash
npm install --save-dev @next/bundle-analyzer
```

Add to `next.config.js`:

```javascript
const withBundleAnalyzer = require('@next/bundle-analyzer')({
  enabled: process.env.ANALYZE === 'true',
});

module.exports = withBundleAnalyzer(nextConfig);
```

Run: `ANALYZE=true npm run build`

3. **Check for duplicate dependencies:**

```bash
npm dedupe
```

---

## Quick Fix Checklist

- [ ] Update CSP in `next.config.js` to allow localhost
- [ ] Generate PWA icons or remove icon references from manifest
- [ ] Fix font loading (use Next.js fonts or remove preload)
- [ ] Update Service Worker to handle missing assets gracefully
- [ ] Remove preload links for non-existent resources
- [ ] Analyze and optimize bundle size
- [ ] Test in development mode
- [ ] Verify all API calls work

---

## Testing After Fixes

1. **Clear browser cache and service workers:**
   - Chrome DevTools → Application → Clear storage
   - Unregister all service workers

2. **Restart dev server:**

   ```bash
   cd frontend
   npm run dev
   ```

3. **Check console for errors:**
   - Should see no CSP violations
   - Should see no 404 errors
   - API calls should work

4. **Test PWA:**
   - Check manifest loads correctly
   - Verify icons display (or are gracefully absent)
   - Test offline functionality

---

## Priority Order

1. **Critical (Do First):** Fix CSP - blocks all functionality
2. **High:** Fix Service Worker - causes repeated errors
3. **Medium:** Generate icons - improves UX
4. **Low:** Optimize bundle size - performance improvement

---

## Additional Notes

- The CSP issue is the most critical - it's blocking all API communication
- Consider using environment variables to manage CSP policies per environment
- For production, ensure you have proper icons before deploying
- The bundle size warning suggests you might want to audit your dependencies
