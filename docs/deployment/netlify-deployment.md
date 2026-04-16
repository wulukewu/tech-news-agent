# Netlify Deployment Guide

## 問題診斷與解決

### 常見 404 錯誤原因

1. **錯誤的 output 設定**
   - ❌ `output: 'standalone'` 是給 Docker 使用的
   - ✅ Netlify 部署時應該移除或註解掉這個設定

2. **錯誤的 publish 目錄**
   - ✅ Next.js 使用 `.next` 作為 publish 目錄
   - ⚠️ 確保有安裝 `@netlify/plugin-nextjs` plugin

3. **錯誤的 redirects 設定**
   - ❌ 不要使用 `to = "/index.html"` (這是給 SPA 用的)
   - ✅ Next.js plugin 會自動處理路由

## 正確的配置

### netlify.toml

```toml
[build]
  base = "frontend/"
  command = "npm run build"
  publish = ".next"

[[plugins]]
  package = "@netlify/plugin-nextjs"

[build.environment]
  NODE_VERSION = "20"
```

### next.config.js

```javascript
const nextConfig = {
  // 移除或註解掉 output: 'standalone'
  // output: 'standalone',  // 只在 Docker 部署時使用
  reactStrictMode: true,
  // ... 其他設定
};
```

## 部署步驟

### 1. 在 Netlify 上設定專案

1. 連接 GitHub repository
2. 設定 Build settings:
   - **Base directory**: `frontend`
   - **Build command**: `npm run build`
   - **Publish directory**: `.next`

### 2. 安裝 Next.js Plugin

在 Netlify UI 中:

1. 前往 Site settings → Build & deploy → Build plugins
2. 搜尋並安裝 `@netlify/plugin-nextjs`

或在 `netlify.toml` 中已經配置好了。

### 3. 設定環境變數

在 Netlify UI 中設定:

- `NEXT_PUBLIC_API_BASE_URL`: 你的後端 API URL
- `NEXT_PUBLIC_APP_NAME`: 應用程式名稱

### 4. 觸發重新部署

修改配置後:

1. Commit 並 push 到 GitHub
2. Netlify 會自動觸發新的部署
3. 或在 Netlify UI 中手動觸發 "Trigger deploy"

## 驗證部署

部署完成後檢查:

```bash
# 檢查首頁
curl -I https://your-site.netlify.app/

# 檢查 Next.js 路由
curl -I https://your-site.netlify.app/news
curl -I https://your-site.netlify.app/settings

# 應該都返回 200 OK
```

## 常見問題排查

### 問題 1: 仍然出現 404

**解決方案**:

1. 確認 `next.config.js` 中沒有 `output: 'standalone'`
2. 清除 Netlify 的 build cache: Site settings → Build & deploy → Clear cache and retry deploy
3. 檢查 build logs 是否有錯誤

### 問題 2: API 請求失敗 (CORS)

**解決方案**:
在 `netlify.toml` 中設定 API proxy:

```toml
[[redirects]]
  from = "/api/*"
  to = "https://your-backend.onrender.com/api/:splat"
  status = 200
  force = true
```

### 問題 3: 環境變數未生效

**解決方案**:

1. 確認環境變數名稱以 `NEXT_PUBLIC_` 開頭
2. 在 Netlify UI 中設定環境變數
3. 重新部署

## Docker vs Netlify 配置

如果你需要同時支援 Docker 和 Netlify 部署:

```javascript
// next.config.js
const nextConfig = {
  // 根據環境變數決定 output 模式
  ...(process.env.DEPLOYMENT_TARGET === 'docker' && {
    output: 'standalone',
  }),
  // ... 其他設定
};
```

然後在 Docker 部署時設定 `DEPLOYMENT_TARGET=docker`。

## 參考資源

- [Netlify Next.js Plugin](https://github.com/netlify/netlify-plugin-nextjs)
- [Next.js Deployment Documentation](https://nextjs.org/docs/deployment)
- [Netlify Configuration](https://docs.netlify.com/configure-builds/file-based-configuration/)
