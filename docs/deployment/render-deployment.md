# Render 部署指南

本指南說明如何在 Render 平台上部署 Tech News Agent 應用程式。

## 📋 前置需求

- Render 帳號
- GitHub 儲存庫已連接到 Render
- 環境變數準備完成

## 🚀 快速部署

### 方法 1: 使用 render.yaml（推薦）

1. **連接 GitHub 儲存庫**
   - 登入 [Render Dashboard](https://dashboard.render.com/)
   - 點擊 "New" → "Blueprint"
   - 選擇你的 GitHub 儲存庫
   - Render 會自動偵測 `render.yaml` 並創建所有服務

2. **設定環境變數**

   Frontend 環境變數：

   ```
   NEXT_PUBLIC_API_BASE_URL=https://your-backend.onrender.com
   ```

   Backend 環境變數：

   ```
   DATABASE_URL=postgresql://...
   REDIS_URL=redis://...
   SECRET_KEY=（自動生成）
   ```

3. **部署**
   - 點擊 "Apply" 開始部署
   - 等待構建完成（首次約 5-10 分鐘）

### 方法 2: 手動創建服務

#### Frontend (Next.js)

1. **創建 Web Service**
   - Name: `tech-news-agent-frontend`
   - Runtime: `Node`
   - Build Command:
     ```bash
     npm install && NODE_OPTIONS='--max-old-space-size=4096' npm run build
     ```
   - Start Command:
     ```bash
     npm start
     ```
   - Root Directory: `frontend`

2. **環境變數**
   ```
   NODE_VERSION=20
   NODE_ENV=production
   NEXT_PUBLIC_API_BASE_URL=https://your-backend.onrender.com
   ```

#### Backend (FastAPI)

1. **創建 Web Service**
   - Name: `tech-news-agent-backend`
   - Runtime: `Python 3`
   - Build Command:
     ```bash
     pip install -r requirements.txt
     ```
   - Start Command:
     ```bash
     uvicorn app.main:app --host 0.0.0.0 --port $PORT
     ```
   - Root Directory: `backend`

2. **環境變數**
   ```
   PYTHON_VERSION=3.11
   ENVIRONMENT=production
   DATABASE_URL=postgresql://...
   REDIS_URL=redis://...
   ```

## 🔧 記憶體不足問題解決方案

### 問題症狀

收到類似以下的錯誤郵件：

```
FATAL ERROR: Ineffective mark-compacts near heap limit
Allocation failed - JavaScript heap out of memory
```

### 解決方案

#### 方法 1: Docker 部署（推薦用於 Render）

如果你在 Render 上使用 Docker 部署，記憶體設定已經在 `frontend/Dockerfile` 中配置好了：

```dockerfile
# Build environment variables
ENV NODE_OPTIONS="--max-old-space-size=4096"

# Build application with increased memory
RUN NODE_OPTIONS="--max-old-space-size=4096" npm run build
```

**Render 上的 Docker 設定**：

1. 進入 Render Dashboard → 你的服務
2. 確認 **Environment** 設定為 `Docker`
3. **Dockerfile Path**: `frontend/Dockerfile`
4. 不需要額外設定，重新部署即可

**本地測試**：

```bash
# 測試 Docker 構建是否成功
cd frontend
docker build -t tech-news-frontend .
```

#### 方法 2: Node.js 原生部署

如果你使用 Node.js 環境（非 Docker），在 Render Dashboard 設定：

**Build Command**：

```bash
npm install && NODE_OPTIONS='--max-old-space-size=4096' npm run build
```

**Start Command**：

```bash
npm start
```

#### 方法 3: 本地開發

`package.json` 已經配置好記憶體設定：

```json
{
  "scripts": {
    "dev": "NODE_OPTIONS='--max-old-space-size=4096' next dev",
    "build": "NODE_OPTIONS='--max-old-space-size=4096' npm run build"
  }
}
```

這會將 Node.js heap 記憶體增加到 4GB。

#### 方法 4: 升級 Render 方案

如果問題持續發生，考慮升級方案：

| 方案     | 記憶體 | 價格   |
| -------- | ------ | ------ |
| Starter  | 512 MB | 免費   |
| Standard | 2 GB   | $7/月  |
| Pro      | 4 GB   | $25/月 |

**建議**: 對於 Next.js 應用，至少使用 Standard 方案。

#### 3. 優化構建過程

在 `render.yaml` 中已配置：

```yaml
buildCommand: npm install && NODE_OPTIONS='--max-old-space-size=4096' npm run build
```

#### 4. 清除構建快取

如果問題持續：

1. 進入 Render Dashboard
2. 選擇你的服務
3. 點擊 "Manual Deploy" → "Clear build cache & deploy"

## 📊 監控與除錯

### 查看日誌

```bash
# 在 Render Dashboard 中
Services → [Your Service] → Logs
```

### 常見錯誤

#### 1. 構建超時

```
Build exceeded maximum time limit
```

**解決方案**:

- 升級到 Standard 方案
- 優化 `node_modules` 快取

#### 2. 記憶體不足

```
JavaScript heap out of memory
```

**解決方案**:

- 已在 `package.json` 中配置 `NODE_OPTIONS`
- 考慮升級方案

#### 3. 環境變數未設定

```
Error: NEXT_PUBLIC_API_BASE_URL is not defined
```

**解決方案**:

- 在 Render Dashboard 中設定環境變數
- 重新部署

## 🔄 自動部署

### 設定自動部署

1. **連接 GitHub**
   - Render 會自動偵測 `main` 分支的推送
   - 每次推送都會觸發新的部署

2. **設定部署分支**

   ```yaml
   # render.yaml
   services:
     - type: web
       autoDeploy: true
       branch: main # 或其他分支
   ```

3. **部署通知**
   - 在 Render Dashboard 設定 Slack/Discord webhook
   - 接收部署成功/失敗通知

## 🔐 安全性設定

### 環境變數管理

**不要**將敏感資訊提交到 Git：

```bash
# .gitignore 已包含
.env
.env.local
.env.production
```

**使用** Render 的環境變數功能：

- Dashboard → Service → Environment
- 使用 "Generate Value" 生成安全的密鑰

### HTTPS

Render 自動提供免費的 SSL 憑證：

- 自動更新
- 支援自訂網域

## 📈 效能優化

### 1. 啟用 CDN

Render 自動提供全球 CDN：

- 靜態資源自動快取
- 自動壓縮

### 2. 資料庫連接池

```python
# backend/app/database.py
engine = create_engine(
    DATABASE_URL,
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True
)
```

### 3. Redis 快取

使用 Render 的 Redis 服務：

- 快取 API 回應
- Session 儲存

## 🆘 疑難排解

### 構建失敗

1. **檢查日誌**

   ```bash
   # 在 Render Dashboard 查看完整日誌
   ```

2. **本地測試**

   ```bash
   # 模擬 Render 構建環境
   cd frontend
   NODE_OPTIONS='--max-old-space-size=4096' npm run build
   ```

3. **清除快取**
   - Manual Deploy → Clear build cache & deploy

### 運行時錯誤

1. **檢查環境變數**

   ```bash
   # 確認所有必要的環境變數都已設定
   ```

2. **檢查健康檢查**

   ```bash
   curl https://your-app.onrender.com/health
   ```

3. **查看錯誤日誌**
   - Dashboard → Logs → Filter by "error"

## 📚 相關資源

- [Render 官方文件](https://render.com/docs)
- [Next.js 部署指南](https://nextjs.org/docs/deployment)
- [FastAPI 部署最佳實踐](https://fastapi.tiangolo.com/deployment/)

## 💡 最佳實踐

1. **使用 Blueprint (render.yaml)**
   - 版本控制部署配置
   - 一鍵部署所有服務

2. **設定健康檢查**
   - 確保服務正常運行
   - 自動重啟失敗的服務

3. **監控資源使用**
   - 定期檢查記憶體和 CPU 使用率
   - 適時升級方案

4. **備份資料庫**
   - 使用 Render 的自動備份功能
   - 定期測試還原流程

5. **使用環境變數**
   - 不同環境使用不同配置
   - 敏感資訊不提交到 Git

---

**需要協助？** 查看 [Render 社群論壇](https://community.render.com/) 或聯繫支援團隊。
