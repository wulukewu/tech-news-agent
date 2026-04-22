# 部署檢查清單

## 📋 部署前檢查

### ✅ 環境變數設定

#### Backend (.env)

- [ ] `SUPABASE_URL` - 已設定正確的 Supabase URL
- [ ] `SUPABASE_KEY` - 已設定 service_role key (非 anon key)
- [ ] `DISCORD_TOKEN` - 已設定 Discord bot token
- [ ] `DISCORD_CHANNEL_ID` - 已設定正確的頻道 ID
- [ ] `DISCORD_CLIENT_ID` - 已設定 OAuth2 Client ID
- [ ] `DISCORD_CLIENT_SECRET` - 已設定 OAuth2 Client Secret
- [ ] `DISCORD_REDIRECT_URI` - 已更新為正式網域
- [ ] `GROQ_API_KEY` - 已設定 Groq API key
- [ ] `JWT_SECRET` - 已設定強密碼 (至少 32 字元)
- [ ] `CORS_ORIGINS` - 已更新為正式網域
- [ ] `COOKIE_SECURE` - 已設定為 `true`

#### Frontend (.env.local)

- [ ] `NEXT_PUBLIC_API_BASE_URL` - 已更新為正式 API 網域
- [ ] 其他環境變數已正確設定

### ✅ Docker 配置

- [ ] 已測試 `docker-compose.prod.yml` 在本地運行
- [ ] Port 映射符合伺服器配置
- [ ] Network 設定正確
- [ ] Volume 掛載路徑存在且有權限

### ✅ 安全性檢查

- [ ] 所有 `.env` 檔案已加入 `.gitignore`
- [ ] 沒有硬編碼的密碼或 API key
- [ ] HTTPS 已啟用 (使用 Nginx/Caddy)
- [ ] CORS 設定僅允許信任的網域
- [ ] JWT_SECRET 使用強隨機密碼
- [ ] Cookie secure flag 已啟用

### ✅ 資料庫檢查

- [ ] Supabase 資料庫已初始化 (`init_supabase.sql`)
- [ ] 預設 RSS feeds 已載入 (`seed_feeds.py`)
- [ ] 資料庫連線測試成功
- [ ] 備份策略已設定

### ✅ 程式碼檢查

- [ ] 所有測試通過
- [ ] 沒有 console.log 或除錯程式碼
- [ ] 程式碼已 commit 並 push 到 Git
- [ ] 版本標籤已建立

---

## 🚀 部署步驟

### 1. 準備伺服器

```bash
# 更新系統
sudo apt update && sudo apt upgrade -y

# 安裝 Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# 安裝 Docker Compose
sudo apt install docker-compose-plugin -y

# 驗證安裝
docker --version
docker compose version
```

### 2. 複製專案

```bash
# Clone repository
git clone <your-repo-url>
cd tech-news-agent

# 或使用 rsync 從本地複製
rsync -avz --exclude 'node_modules' --exclude '.next' \
  ./ user@server:/path/to/tech-news-agent/
```

### 3. 設定環境變數

```bash
# 複製範本
cp .env.example .env

# 編輯並填入正式環境變數
nano .env
```

**重要:** 詳細的環境變數說明請參考 [ENV_SETUP_GUIDE.md](./ENV_SETUP_GUIDE.md)

### 4. 建置並啟動

```bash
# 建置映像檔
docker compose -f docker-compose.prod.yml build

# 啟動服務
docker compose -f docker-compose.prod.yml up -d

# 查看日誌
docker compose -f docker-compose.prod.yml logs -f
```

### 5. 驗證部署

```bash
# 檢查容器狀態
docker compose -f docker-compose.prod.yml ps

# 測試 Backend API
curl http://localhost:8000/health

# 測試 Frontend
curl http://localhost:3000
```

### 6. 設定反向代理 (Nginx)

```nginx
# /etc/nginx/sites-available/tech-news-agent

# Frontend
server {
    listen 80;
    server_name yourdomain.com;

    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
}

# Backend API
server {
    listen 80;
    server_name api.yourdomain.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

```bash
# 啟用站點
sudo ln -s /etc/nginx/sites-available/tech-news-agent \
           /etc/nginx/sites-enabled/

# 測試配置
sudo nginx -t

# 重新載入 Nginx
sudo systemctl reload nginx
```

### 7. 設定 SSL (Let's Encrypt)

```bash
# 安裝 Certbot
sudo apt install certbot python3-certbot-nginx -y

# 取得 SSL 憑證
sudo certbot --nginx -d yourdomain.com -d api.yourdomain.com

# 測試自動更新
sudo certbot renew --dry-run
```

---

## 🔄 更新部署

### 方法 1: 手動更新

```bash
# 1. 拉取最新程式碼
git pull origin main

# 2. 停止服務
docker compose -f docker-compose.prod.yml down

# 3. 重新建置
docker compose -f docker-compose.prod.yml build

# 4. 啟動服務
docker compose -f docker-compose.prod.yml up -d

# 5. 查看日誌
docker compose -f docker-compose.prod.yml logs -f
```

### 方法 2: 使用 Makefile

```bash
# 一鍵更新
make down-prod && git pull && make up-prod
```

### 方法 3: 零停機更新 (使用 Docker Compose)

```bash
# 建置新映像檔
docker compose -f docker-compose.prod.yml build

# 滾動更新 (一次更新一個容器)
docker compose -f docker-compose.prod.yml up -d --no-deps --build backend
docker compose -f docker-compose.prod.yml up -d --no-deps --build frontend
```

---

## 📊 監控與維護

### 日誌管理

```bash
# 查看即時日誌
docker compose -f docker-compose.prod.yml logs -f

# 查看特定服務日誌
docker compose -f docker-compose.prod.yml logs -f backend
docker compose -f docker-compose.prod.yml logs -f frontend

# 查看最近 100 行
docker compose -f docker-compose.prod.yml logs --tail=100

# 日誌輪替 (在 docker-compose.prod.yml 中設定)
logging:
  driver: "json-file"
  options:
    max-size: "10m"
    max-file: "3"
```

### 健康檢查

```bash
# 檢查容器狀態
docker compose -f docker-compose.prod.yml ps

# 檢查容器資源使用
docker stats

# 檢查磁碟使用
docker system df
```

### 備份

```bash
# 備份日誌
tar -czf logs-backup-$(date +%Y%m%d).tar.gz backend/logs/

# 備份環境變數 (小心處理)
tar -czf env-backup-$(date +%Y%m%d).tar.gz \
  backend/.env frontend/.env.local
```

### 清理

```bash
# 清理未使用的映像檔
docker image prune -a

# 清理未使用的容器
docker container prune

# 清理未使用的 volumes
docker volume prune

# 完整清理
docker system prune -a --volumes
```

---

## 🐛 疑難排解

### 容器無法啟動

```bash
# 查看詳細錯誤
docker compose -f docker-compose.prod.yml logs

# 檢查配置
docker compose -f docker-compose.prod.yml config

# 重新建置
docker compose -f docker-compose.prod.yml build --no-cache
```

### Port 衝突

```bash
# 檢查 port 使用
sudo netstat -tulpn | grep :3000
sudo netstat -tulpn | grep :8000

# 修改 docker-compose.prod.yml 中的 port 映射
```

### 記憶體不足

```bash
# 檢查記憶體使用
docker stats

# 限制容器記憶體 (在 docker-compose.prod.yml)
services:
  backend:
    mem_limit: 512m
  frontend:
    mem_limit: 512m
```

### 網路問題

```bash
# 檢查網路
docker network ls
docker network inspect tech-news-network

# 重建網路
docker compose -f docker-compose.prod.yml down
docker network prune
docker compose -f docker-compose.prod.yml up -d
```

---

## 📈 效能優化

### Docker 優化

- [ ] 使用 `.dockerignore` 減少建置上下文
- [ ] 多階段建置減少映像檔大小
- [ ] 使用 Alpine 基礎映像檔
- [ ] 快取 Docker layers

### 應用程式優化

- [ ] 啟用 Gzip 壓縮
- [ ] 使用 CDN 提供靜態資源
- [ ] 設定適當的快取標頭
- [ ] 優化資料庫查詢

### 伺服器優化

- [ ] 設定防火牆規則
- [ ] 啟用 fail2ban
- [ ] 定期更新系統
- [ ] 監控資源使用

---

## 🔒 安全性最佳實踐

- [ ] 定期更新 Docker 和依賴套件
- [ ] 使用非 root 使用者運行容器
- [ ] 限制容器權限
- [ ] 定期掃描映像檔漏洞
- [ ] 設定適當的網路隔離
- [ ] 啟用 Docker Content Trust
- [ ] 定期備份資料
- [ ] 監控異常活動

---

## 📞 支援資源

- [Docker 文件](https://docs.docker.com/)
- [Next.js 部署指南](https://nextjs.org/docs/deployment)
- [FastAPI 部署指南](https://fastapi.tiangolo.com/deployment/)
- [Nginx 文件](https://nginx.org/en/docs/)
- [Let's Encrypt 文件](https://letsencrypt.org/docs/)
