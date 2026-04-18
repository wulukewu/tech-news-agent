# Docker 優化報告

## 優化結果

| 指標             | 優化前       | 優化後         | 改善                  |
| ---------------- | ------------ | -------------- | --------------------- |
| **Image 大小**   | 253 MB       | 166 MB         | **-34%** (減少 87 MB) |
| **Base Image**   | node:20-slim | node:20-alpine | 更輕量                |
| **Build Layers** | 複雜         | 簡化           | 更快的 cache          |

## 主要優化項目

### 1. 使用 Alpine Linux

```dockerfile
# 優化前
FROM node:20-slim AS base

# 優化後
FROM node:20-alpine AS base
```

- Alpine 比 Debian slim 更小（~5MB vs ~40MB）
- 足夠運行 Node.js 應用

### 2. 移除不必要的 Build Tools

```dockerfile
# 優化前 - 安裝 Python, make, g++
RUN apt-get update && apt-get install -y \
    python3 \
    make \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# 優化後 - 不需要這些工具
# Next.js 不需要 native compilation
```

### 3. 簡化 Layer 結構

```dockerfile
# 優化前 - 多個 RUN 指令
RUN groupadd --system --gid 1001 nodejs
RUN useradd --system --uid 1001 nextjs
RUN mkdir .next
RUN chown nextjs:nodejs .next

# 優化後 - 合併指令
RUN addgroup --system --gid 1001 nodejs && \
    adduser --system --uid 1001 nextjs
```

### 4. 使用 .dockerignore 排除測試檔案

排除了：

- `__tests__/` - 測試目錄
- `*.test.ts`, `*.spec.ts` - 測試檔案
- `coverage/` - 測試覆蓋率報告
- `vitest.config.ts`, `jest.config.js` - 測試配置
- `playwright.config.ts` - E2E 測試配置
- `docs/`, `*.md` - 文件
- `.vscode/`, `.idea/` - IDE 配置

### 5. 環境變數優化

```dockerfile
# 優化後 - 使用 multi-line ENV
ENV NODE_ENV=production \
    NEXT_TELEMETRY_DISABLED=1 \
    PORT=3000 \
    HOSTNAME="0.0.0.0"
```

## Build 速度優化

### Cache 策略

1. **Dependencies Layer** - 只在 package.json 改變時重建
2. **Build Layer** - 只在源碼改變時重建
3. **Runtime Layer** - 只複製必要的 production 檔案

### 建議的 Build 指令

```bash
# 使用 BuildKit 加速
DOCKER_BUILDKIT=1 docker build \
  --build-arg NEXT_PUBLIC_API_BASE_URL=https://api.example.com \
  --build-arg NEXT_PUBLIC_APP_NAME="Tech News Agent" \
  --build-arg NEXT_PUBLIC_APP_URL=https://example.com \
  -t tech-news-frontend:latest \
  .
```

## 測試與 CI/CD 分離

### 原則

- ✅ **Production Image**: 只包含運行時需要的檔案
- ✅ **測試在 CI/CD 執行**: 不在 Docker build 中執行測試
- ✅ **Linting 在開發環境**: 本地開發時檢查

### CI/CD Pipeline 建議

```yaml
# .github/workflows/ci.yml
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
      - run: npm ci
      - run: npm run lint
      - run: npm run type-check
      - run: npm run test
      - run: npm run test:e2e

  build:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - run: docker build -t app:${{ github.sha }} .
```

## 進一步優化建議

### 1. 使用 Multi-stage Build Cache

```bash
# 使用 cache mount 加速 npm install
RUN --mount=type=cache,target=/root/.npm \
    npm ci
```

### 2. 考慮使用 Distroless Image

```dockerfile
# 更小更安全的 runtime
FROM gcr.io/distroless/nodejs20-debian12
```

### 3. 壓縮 Static Assets

```javascript
// next.config.js
module.exports = {
  compress: true,
  generateBuildId: async () => {
    return process.env.BUILD_ID || 'build';
  },
};
```

## 安全性改善

1. ✅ 使用 non-root user (nextjs)
2. ✅ 最小化 attack surface (Alpine)
3. ✅ 不包含開發工具
4. ✅ 不包含測試檔案
5. ✅ 禁用 telemetry

## 總結

優化後的 Dockerfile：

- **更小**: 166 MB vs 253 MB (-34%)
- **更快**: 更好的 layer caching
- **更簡單**: 更少的指令和依賴
- **更安全**: 最小化的 attack surface
- **更專注**: 只包含 production 需要的檔案

測試和開發工具應該在 CI/CD pipeline 和本地開發環境中使用，不應該包含在 production image 中。
