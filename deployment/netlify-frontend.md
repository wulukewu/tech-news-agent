# Next.js Frontend 部署到 Netlify (免費版)

## 前置準備

確保你的 Next.js 專案在 `frontend/` 資料夾。

## 步驟 1: 安裝 Netlify Next.js Plugin

```bash
cd frontend
npm install -D @netlify/plugin-nextjs
```

## 步驟 2: 創建 Netlify 配置

在**專案根目錄**創建 `netlify.toml`：

```toml
# netlify.toml
[build]
  base = "frontend/"
  command = "npm run build"
  publish = ".next"

[[plugins]]
  package = "@netlify/plugin-nextjs"

[build.environment]
  NODE_VERSION = "18"
  NPM_FLAGS = "--legacy-peer-deps"

# 環境變數 (也可以在 Netlify Dashboard 設定)
[context.production.environment]
  NEXT_PUBLIC_API_URL = "https://your-app-backend.onrender.com"
  NEXT_PUBLIC_API_TIMEOUT = "30000"

[context.deploy-preview.environment]
  NEXT_PUBLIC_API_URL = "https://your-app-backend.onrender.com"

# 重定向規則 - 處理 Next.js 路由
[[redirects]]
  from = "/*"
  to = "/index.html"
  status = 200

# API 代理 (可選) - 避免 CORS 問題
[[redirects]]
  from = "/api/*"
  to = "https://your-app-backend.onrender.com/api/:splat"
  status = 200
  force = true
  headers = {X-From = "Netlify"}

# 自訂 Headers
[[headers]]
  for = "/*"
  [headers.values]
    X-Frame-Options = "DENY"
    X-XSS-Protection = "1; mode=block"
    X-Content-Type-Options = "nosniff"
    Referrer-Policy = "strict-origin-when-cross-origin"

# 快取靜態資源
[[headers]]
  for = "/_next/static/*"
  [headers.values]
    Cache-Control = "public, max-age=31536000, immutable"
```

## 步驟 3: 更新 Next.js 配置

```javascript
// frontend/next.config.js
/** @type {import('next').NextConfig} */
const nextConfig = {
  // Netlify 建議使用 standalone 輸出
  output: 'standalone',

  // 環境變數
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL,
    NEXT_PUBLIC_API_TIMEOUT: process.env.NEXT_PUBLIC_API_TIMEOUT,
  },

  // 圖片優化
  images: {
    domains: ['your-app-backend.onrender.com'],
    // Netlify 使用自己的圖片優化
    unoptimized: false,
  },

  // 如果使用 App Router
  experimental: {
    serverActions: true,
  },
};

module.exports = nextConfig;
```

## 步驟 4: 更新 package.json

確保有正確的建置腳本：

```json
{
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start",
    "lint": "next lint"
  },
  "dependencies": {
    "next": "^14.0.0",
    "react": "^18.2.0",
    "react-dom": "^18.2.0"
  },
  "devDependencies": {
    "@netlify/plugin-nextjs": "^5.0.0",
    "typescript": "^5.0.0"
  }
}
```

## 步驟 5: 部署到 Netlify

### 方法 A: 透過 Netlify Dashboard (推薦)

1. 前往 [netlify.com](https://netlify.com)
2. 點擊 "Add new site" → "Import an existing project"
3. 連接 GitHub repository
4. 配置：
   - **Base directory**: `frontend`
   - **Build command**: `npm run build` (自動偵測)
   - **Publish directory**: `.next` (自動偵測)
   - **Functions directory**: (留空，由 plugin 處理)

5. 設定環境變數：

   ```
   NEXT_PUBLIC_API_URL=https://your-app-backend.onrender.com
   NEXT_PUBLIC_API_TIMEOUT=30000
   NODE_VERSION=18
   ```

6. 點擊 "Deploy site"

### 方法 B: 透過 Netlify CLI

```bash
# 安裝 Netlify CLI
npm install -g netlify-cli

# 登入
netlify login

# 在專案根目錄初始化
netlify init

# 部署
netlify deploy --prod
```

## 步驟 6: 配置 API 代理 (推薦)

使用 Netlify 的重定向功能避免 CORS 問題：

```toml
# netlify.toml
[[redirects]]
  from = "/api/*"
  to = "https://your-app-backend.onrender.com/api/:splat"
  status = 200
  force = true
```

然後在前端使用相對路徑：

```typescript
// frontend/lib/api/client.ts
const API_URL =
  process.env.NODE_ENV === 'production'
    ? '/api' // 使用 Netlify 代理
    : 'http://localhost:8000/api';

export const apiClient = {
  async fetch(endpoint: string, options?: RequestInit) {
    const response = await fetch(`${API_URL}${endpoint}`, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options?.headers,
      },
    });

    if (!response.ok) {
      throw new Error(`API Error: ${response.status}`);
    }

    return response.json();
  },
};
```

## 步驟 7: 處理 Render 冷啟動

在前端添加載入狀態：

```typescript
// frontend/components/ui/loading-overlay.tsx
'use client';

import { useEffect, useState } from 'react';

export function LoadingOverlay() {
  const [isWarmingUp, setIsWarmingUp] = useState(false);

  useEffect(() => {
    // 檢測 API 是否需要喚醒
    const checkAPI = async () => {
      try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 5000);

        await fetch('/api/health', { signal: controller.signal });
        clearTimeout(timeoutId);
      } catch (error) {
        setIsWarmingUp(true);
        // 顯示載入訊息
      }
    };

    checkAPI();
  }, []);

  if (!isWarmingUp) return null;

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-white p-6 rounded-lg shadow-xl">
        <div className="animate-spin h-8 w-8 border-4 border-blue-500 border-t-transparent rounded-full mx-auto mb-4" />
        <p className="text-gray-700">後端正在啟動中，請稍候...</p>
        <p className="text-sm text-gray-500 mt-2">首次載入約需 20-30 秒</p>
      </div>
    </div>
  );
}
```

## Netlify 特色功能

### 1. 表單處理 (免費 100 次/月)

```html
<!-- 不需要後端處理表單 -->
<form name="contact" method="POST" data-netlify="true">
  <input type="hidden" name="form-name" value="contact" />
  <input type="email" name="email" required />
  <textarea name="message" required></textarea>
  <button type="submit">送出</button>
</form>
```

### 2. Split Testing

在 Netlify Dashboard 可以 A/B 測試不同版本。

### 3. Deploy Previews

每個 PR 自動創建預覽 URL。

### 4. Edge Functions (進階)

```typescript
// netlify/edge-functions/hello.ts
export default async (request: Request) => {
  return new Response('Hello from the edge!');
};

export const config = { path: '/edge-hello' };
```

## 免費版限制

- ✅ **100GB 頻寬/月** (通常足夠)
- ✅ **300 分鐘建置時間/月**
- ✅ **125k Serverless Function 請求/月**
- ⚠️ **建置時間較長** (比 Vercel 慢一些)
- ⚠️ **Next.js 新功能支援較慢**

## 監控與除錯

### 查看建置日誌

Dashboard → Deploys → 點擊部署 → Deploy log

### 查看 Function 日誌

Dashboard → Functions → 點擊 function → Logs

### 即時日誌

```bash
netlify dev  # 本地開發
netlify logs # 查看 production 日誌
```

## 效能優化

### 1. 啟用 Netlify 圖片 CDN

```javascript
// next.config.js
module.exports = {
  images: {
    loader: 'custom',
    loaderFile: './netlify-image-loader.js',
  },
};
```

```javascript
// netlify-image-loader.js
export default function netlifyLoader({ src, width, quality }) {
  return `${src}?w=${width}&q=${quality || 75}`;
}
```

### 2. 預渲染靜態頁面

```typescript
// app/blog/page.tsx
export const dynamic = 'force-static';

export default function BlogPage() {
  return <div>Blog</div>;
}
```

### 3. 使用 ISR

```typescript
export const revalidate = 3600; // 每小時重新生成
```

## 驗證部署

```bash
# 測試網站
curl https://your-app.netlify.app

# 測試 API 代理
curl https://your-app.netlify.app/api/health
```

## 常見問題

### Q: Next.js 14 App Router 支援嗎？

A: 支援，但確保使用最新版 `@netlify/plugin-nextjs`

### Q: 如何設定自訂網域？

A: Dashboard → Domain settings → Add custom domain

### Q: 建置失敗怎麼辦？

A: 檢查 Node 版本、依賴版本、建置日誌

### Q: 如何回滾？

A: Dashboard → Deploys → 選擇舊版本 → Publish deploy

## 成本

- ✅ **完全免費** (個人和商業專案都可以)
- 超過限制才需付費

## 升級選項

- **Pro Plan**: $19/月 (1TB 頻寬)
- **Business Plan**: $99/月 (團隊功能)

## Netlify vs Vercel 比較

| 功能         | Netlify | Vercel    |
| ------------ | ------- | --------- |
| Next.js 整合 | 良好    | 完美      |
| 免費頻寬     | 100GB   | 100GB     |
| 商業使用     | ✅ 免費 | ⚠️ 需付費 |
| 表單處理     | ✅ 內建 | ❌ 需自建 |
| 建置速度     | 較慢    | 較快      |
| 新功能支援   | 較慢    | 最快      |

**結論**: 如果你重視免費商業使用和表單功能，Netlify 是好選擇！
