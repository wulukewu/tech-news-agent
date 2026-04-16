# Netlify 部署問題修復總結

## 修復日期

2026-04-17

## 問題概述

Netlify 部署失敗，出現兩個主要錯誤：

1. **404 Page Not Found** - 所有頁面都無法訪問
2. **Build Error: Duplicate Routes** - 路由衝突導致編譯失敗

## 根本原因

### 問題 1: 404 錯誤

- **原因**: `next.config.js` 中的 `output: 'standalone'` 設定
- **說明**: 這個設定是為 Docker 部署設計的，會產生獨立的伺服器檔案，不適用於 Netlify 的靜態部署

### 問題 2: 路由衝突

- **原因**: 重複的頁面檔案導致相同的 URL 路徑
- **具體**:
  - `app/(dashboard)/settings/notifications/page.tsx` → `/settings/notifications`
  - `app/settings/notifications/page.tsx` → `/settings/notifications`
- **說明**: Route groups `(dashboard)` 不影響 URL，所以兩個檔案解析到同一個路徑

## 修復方案

### 1. 修復 next.config.js

**修改前**:

```javascript
const nextConfig = {
  output: 'standalone', // ❌ 導致 404
  reactStrictMode: true,
  // ...
};
```

**修改後**:

```javascript
const nextConfig = {
  // output: 'standalone',  // ✅ 已註解，只在 Docker 使用
  reactStrictMode: true,
  // ...
};
```

### 2. 移除重複路由

**刪除的檔案**:

- `frontend/app/settings/notifications/page.tsx`
- `frontend/app/settings/` 目錄（已清空）

**保留的檔案**:

- `frontend/app/(dashboard)/settings/notifications/page.tsx` ✅

### 3. 創建 netlify.toml

新增正確的 Netlify 配置檔案：

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

## 新增工具

### 1. 配置檢查腳本

- **檔案**: `scripts/check-netlify-config.sh`
- **功能**: 自動檢查 Netlify 配置是否正確
- **使用**: `./scripts/check-netlify-config.sh`

**檢查項目**:

- ✅ netlify.toml 存在且配置正確
- ✅ Next.js plugin 已配置
- ✅ next.config.js 沒有 standalone 設定
- ✅ 沒有重複的路由
- ✅ package.json 配置正確

### 2. 部署文件

- **檔案**: `docs/deployment/netlify-deployment.md`
- **內容**: 完整的 Netlify 部署指南和故障排除

## 驗證結果

### 本地編譯測試

```bash
cd frontend && npm run build
```

**結果**: ✅ 編譯成功

- 無路由衝突錯誤
- 僅有 linting 警告（不影響部署）

### 配置檢查

```bash
./scripts/check-netlify-config.sh
```

**結果**: ✅ 所有檢查通過

## 後續步驟

### 1. 提交變更

```bash
git add .
git commit -m "fix: resolve Netlify deployment issues (404 and duplicate routes)"
git push origin main
```

### 2. 在 Netlify 設定環境變數

前往 Netlify UI → Site settings → Environment variables:

- `NEXT_PUBLIC_API_BASE_URL`: 你的後端 API URL
- `NEXT_PUBLIC_APP_NAME`: Tech News Agent

### 3. 觸發重新部署

- Netlify 會自動偵測 push 並重新部署
- 或手動在 Netlify UI 點擊 "Trigger deploy"

### 4. 驗證部署

```bash
# 檢查首頁
curl -I https://your-site.netlify.app/

# 檢查路由
curl -I https://your-site.netlify.app/articles
curl -I https://your-site.netlify.app/settings/notifications

# 應該都返回 200 OK
```

## 預防措施

### 1. 使用配置檢查腳本

在每次部署前執行：

```bash
./scripts/check-netlify-config.sh
```

### 2. 條件式 output 設定

如果需要同時支援 Docker 和 Netlify：

```javascript
// next.config.js
const nextConfig = {
  ...(process.env.DEPLOYMENT_TARGET === 'docker' && {
    output: 'standalone',
  }),
  // ... 其他設定
};
```

然後在 Docker 部署時設定環境變數：

```bash
DEPLOYMENT_TARGET=docker npm run build
```

### 3. 路由組織原則

- 使用 route groups `(folder)` 來組織程式碼
- 不要在 route group 外創建同名路由
- 定期檢查重複路由：
  ```bash
  find frontend/app -name "page.tsx" -type f | sort
  ```

## 相關文件

- [Netlify Deployment Guide](./netlify-deployment.md)
- [Deployment Checklist](./deployment-checklist.md)
- [Next.js Deployment Docs](https://nextjs.org/docs/deployment)
- [Netlify Next.js Plugin](https://github.com/netlify/netlify-plugin-nextjs)

## 總結

✅ **404 錯誤**: 已修復（移除 standalone 設定）
✅ **路由衝突**: 已修復（刪除重複檔案）
✅ **配置檔案**: 已創建（netlify.toml）
✅ **檢查工具**: 已建立（check-netlify-config.sh）
✅ **文件**: 已更新（部署指南）

現在可以成功部署到 Netlify！🎉
