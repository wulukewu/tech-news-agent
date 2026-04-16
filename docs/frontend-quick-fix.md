# Frontend Quick Fix Guide

## Immediate Actions Required

### 1. Fix CSP (Already Applied) ✅

The Content Security Policy has been updated to allow HTTP localhost connections in development mode.

### 2. Generate Placeholder Icons

Run this command to generate placeholder PWA icons:

```bash
cd frontend
node scripts/generate-placeholder-icons.js
```

**Note:** If you get an error about `sharp` not being installed:

```bash
npm install --save-dev sharp
node scripts/generate-placeholder-icons.js
```

This will create placeholder icons in `frontend/public/icons/` for development.

### 3. Restart Development Server

After making these changes, restart your dev server:

```bash
# Stop the current server (Ctrl+C)
npm run dev
```

### 4. Clear Browser Cache

**Important:** Clear your browser cache and service workers:

1. Open Chrome DevTools (F12)
2. Go to **Application** tab
3. Click **Clear storage** in the left sidebar
4. Check all boxes
5. Click **Clear site data**
6. Go to **Service Workers** section
7. Click **Unregister** on any registered workers
8. Refresh the page (Ctrl+Shift+R or Cmd+Shift+R)

---

## What Was Fixed

### ✅ CSP Policy Updated

- **File:** `frontend/next.config.js`
- **Change:** Added `http://localhost:*` to `connect-src` in development mode
- **Impact:** API calls now work in development

### ✅ Resource Preloading Fixed

- **File:** `frontend/components/PerformanceInitializer.tsx`
- **Change:** Disabled preloading of missing fonts and images
- **Impact:** No more 404 errors for missing resources

### ✅ Service Worker Cache Fixed

- **File:** `frontend/public/sw.js`
- **Change:**
  - Reduced static assets list to only existing files
  - Added error handling to prevent installation failures
  - **Added development mode detection** - bypasses caching on localhost
  - Prevents infinite reload loops in development
- **Impact:** Service Worker works correctly, no reload loops
- **Impact:** Service Worker installs successfully

### ✅ Icon Generator Created

- **File:** `frontend/scripts/generate-placeholder-icons.js`
- **Purpose:** Generate placeholder PWA icons for development
- **Usage:** Run once to create all required icon sizes

---

## Verification Steps

After applying fixes and restarting:

1. **Check Console Errors:**
   - Open DevTools Console (F12)
   - Should see no CSP violations
   - Should see no 404 errors for icons (after generating them)
   - API calls should work

2. **Test API Connection:**
   - Login should work
   - Data should load from backend
   - No "Network Error" messages

3. **Check Service Worker:**
   - DevTools → Application → Service Workers
   - Should show "activated and running"
   - No cache errors in console

4. **Verify PWA Icons:**
   - After generating icons, check `frontend/public/icons/`
   - Should contain PNG files for all sizes
   - Manifest should load without errors

---

## Still Having Issues?

### CSP Still Blocking?

- Check `.env.local` has correct API URL
- Verify backend is running on port 8000
- Try hard refresh (Ctrl+Shift+R)

### Icons Still Missing?

- Run the icon generator script
- Check `frontend/public/icons/` directory
- Verify files were created

### Service Worker Issues?

- Unregister all service workers in DevTools
- Clear all caches
- Hard refresh the page
- Check sw.js loads without errors

### API Not Connecting?

- Verify backend is running: `curl http://localhost:8000/api/health`
- Check CORS settings in backend
- Verify `.env.local` has correct API URL

---

## Production Deployment

Before deploying to production:

1. **Replace Placeholder Icons:**
   - Create professional branded icons
   - Use https://www.pwabuilder.com/imageGenerator
   - Replace all files in `frontend/public/icons/`

2. **Verify CSP:**
   - Production CSP only allows HTTPS
   - Update API URL to production domain
   - Test thoroughly

3. **Test PWA:**
   - Install PWA on mobile device
   - Test offline functionality
   - Verify all icons display correctly

4. **Performance:**
   - Run Lighthouse audit
   - Check bundle size
   - Optimize if needed

---

## Summary

**Critical fixes applied:**

- ✅ CSP allows localhost API in development
- ✅ Removed preloading of missing resources
- ✅ Service Worker handles missing assets gracefully
- ✅ Icon generator script created

**Next steps:**

1. Generate placeholder icons
2. Restart dev server
3. Clear browser cache
4. Test functionality

**For production:**

- Replace placeholder icons with branded ones
- Verify all functionality works
- Run performance audits
