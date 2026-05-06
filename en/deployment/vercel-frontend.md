# Next.js Frontend 部署到 Vercel (免費版)

## 前置準備

確保 `frontend/` 資料夾結構正確：

```
frontend/
├── package.json
├── next.config.js
├── app/ (或 pages/)
└── public/
```

## 步驟 1: 配置環境變數

創建 `frontend/.env.example`：

```bash
# API Configuration
NEXT_PUBLIC_API_URL=https://your-app-backend.onrender.com
NEXT_PUBLIC_API_TIMEOUT=30000

# Optional: Analytics, etc.
```

## 步驟 2: 更新 Next.js 配置

```javascript
// frontend/next.config.js
/** @type {import('next').NextConfig} */
const nextConfig = {
  // 如果使用 App Router
  experimental: {
    serverActions: true,
  },

  // 環境變數
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL,
  },

  // 如果有圖片優化需求
  images: {
    domains: ['your-app-backend.onrender.com'],
  },

  // 輸出配置
  output: 'standalone', // 可選，減少部署大小
};

module.exports = nextConfig;
```

## 步驟 3: 更新 API Client

確保 API client 使用環境變數：

```typescript
// frontend/lib/api/client.ts
const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
const API_TIMEOUT = parseInt(process.env.NEXT_PUBLIC_API_TIMEOUT || '30000');

export const apiClient = {
  async fetch(endpoint: string, options?: RequestInit) {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), API_TIMEOUT);

    try {
      const response = await fetch(`${API_URL}${endpoint}`, {
        ...options,
        signal: controller.signal,
        headers: {
          'Content-Type': 'application/json',
          ...options?.headers,
        },
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        throw new Error(`API Error: ${response.status}`);
      }

      return response.json();
    } catch (error) {
      clearTimeout(timeoutId);

      // 處理冷啟動超時
      if (error.name === 'AbortError') {
        throw new Error('請求超時，後端可能正在啟動中，請稍後再試');
      }

      throw error;
    }
  },
};
```

## 步驟 4: 部署到 Vercel

### 方法 A: 透過 Vercel Dashboard (推薦)

1. 前往 [vercel.com](https://vercel.com)
2. 點擊 "Add New Project"
3. 連接 GitHub repository
4. 配置：
   - **Framework Preset**: Next.js
   - **Root Directory**: `frontend`
   - **Build Command**: `npm run build` (自動偵測)
   - **Output Directory**: `.next` (自動偵測)

5. 設定環境變數：

   ```
   NEXT_PUBLIC_API_URL=https://your-app-backend.onrender.com
   NEXT_PUBLIC_API_TIMEOUT=30000
   ```

6. 點擊 "Deploy"

### 方法 B: 透過 Vercel CLI

```bash
# 安裝 Vercel CLI
npm i -g vercel

# 在 frontend/ 目錄下
cd frontend
vercel login
vercel

# 設定環境變數
vercel env add NEXT_PUBLIC_API_URL production
# 輸入: https://your-app-backend.onrender.com

# 部署
vercel --prod
```

## 步驟 5: 配置自訂網域 (可選)

1. Vercel Dashboard → 你的專案 → Settings → Domains
2. 添加你的網域
3. 更新 DNS 記錄（Vercel 會提供指示）

## 步驟 6: 更新 Backend CORS

在 FastAPI backend 更新 CORS 設定：

```python
# backend/app/main.py
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# 允許 Vercel 網域
origins = [
    "http://localhost:3000",
    "https://your-app.vercel.app",
    "https://your-custom-domain.com",  # 如果有自訂網域
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## 免費版限制

Vercel 免費版非常慷慨：

- ✅ **100GB 頻寬/月** (通常足夠個人專案)
- ✅ **無限部署**
- ✅ **自動 HTTPS**
- ✅ **全球 CDN**
- ✅ **即時預覽** (每個 PR 自動部署)
- ⚠️ **Serverless Function 10 秒限制** (但我們用 Render 處理 backend)
- ⚠️ **商業使用需付費**

## 自動部署

Vercel 會自動：

- ✅ 監聽 `main` 分支推送 → 自動部署到 production
- ✅ 監聽 PR → 自動創建預覽部署
- ✅ 每次部署都有唯一 URL

## 效能優化

### 1. 啟用圖片優化

```jsx
import Image from 'next/image';

<Image
  src="/hero.jpg"
  width={1200}
  height={600}
  alt="Hero"
  priority // 首屏圖片
/>;
```

### 2. 使用 ISR (Incremental Static Regeneration)

```typescript
// app/blog/[slug]/page.tsx
export const revalidate = 3600; // 每小時重新生成

export default async function BlogPost({ params }) {
  const post = await fetchPost(params.slug);
  return <article>{post.content}</article>;
}
```

### 3. 啟用 Edge Runtime (可選)

```typescript
// app/api/hello/route.ts
export const runtime = 'edge';

export async function GET() {
  return Response.json({ message: 'Hello from Edge' });
}
```

## 監控與分析

Vercel 提供免費的：

- **Analytics**: 頁面瀏覽、效能指標
- **Speed Insights**: Core Web Vitals
- **Logs**: 即時日誌查看

在 Dashboard → 你的專案 → Analytics 查看

## 驗證部署

```bash
# 測試 production URL
curl https://your-app.vercel.app

# 測試 API 連接
curl https://your-app.vercel.app/api/test
```

## 常見問題

### Q: 如何回滾到上一個版本？

A: Dashboard → Deployments → 選擇舊版本 → Promote to Production

### Q: 如何查看建置日誌？

A: Dashboard → Deployments → 點擊部署 → Building

### Q: 環境變數更新後需要重新部署嗎？

A: 是的，更新環境變數後需要觸發新的部署

## 成本

- ✅ **完全免費** (個人專案)
- ⚠️ 商業使用需 Pro Plan ($20/月)

## 升級選項

如果超過免費額度：

- **Pro Plan**: $20/月 (1TB 頻寬)
- **Enterprise**: 客製化定價
