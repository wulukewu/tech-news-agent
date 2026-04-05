# Tech News Agent - 文件索引

## 📚 快速導航

### 🚀 快速開始

- [快速開始指南](./QUICKSTART.md) - 最快速的上手方式
- [最終驗證清單](./FINAL_VERIFICATION_CHECKLIST.md) - 功能驗證檢查清單

### ⚙️ 設定指南

- [環境變數設定指南](./setup/ENV_SETUP_GUIDE.md) - 完整的環境變數說明
- [環境變數結構總結](./setup/ENV_STRUCTURE_SUMMARY.md) - 環境變數架構說明
- [環境變數遷移總結](./setup/ENV_MIGRATION_SUMMARY.md) - 遷移歷史記錄
- [OAuth 設定指南](./setup/OAUTH_SETUP_GUIDE.md) - Discord OAuth 設定

### 🐳 Docker 文件

- [Docker 使用指南](./docker/DOCKER_GUIDE.md) - Docker Compose 完整說明
- [Docker 架構說明](./docker/DOCKER_ARCHITECTURE.md) - 開發與正式環境架構
- [Docker 環境比較](./docker/DOCKER_COMPARISON.md) - 開發 vs 正式環境差異

### 🚢 部署文件

- [部署指南](./deployment/DEPLOYMENT.md) - 完整部署流程
- [部署檢查清單](./deployment/DEPLOYMENT_CHECKLIST.md) - 部署前檢查項目

### 📖 使用者與開發者指南

- [使用者指南](./USER_GUIDE.md) - Discord 指令完整說明
- [開發者指南](./DEVELOPER_GUIDE.md) - 架構與開發指南
- [專案概覽](./PROJECT_OVERVIEW.md) - 專案整體說明
- [速率限制指南](./RATE_LIMIT_GUIDE.md) - API 速率限制說明
- [News Now 實作說明](./NEWS_NOW_IMPLEMENTATION.md) - /news_now 功能實作
- [Phase 4 完成總結](./PHASE4_COMPLETION_SUMMARY.md) - 多租戶架構實作總結
- [重構總結](./RESTRUCTURE_SUMMARY.md) - 專案重構記錄
- [遷移指南](./MIGRATION_GUIDE.md) - 資料庫遷移指南

### 🧪 測試文件

- [Supabase 遷移測試](./testing/supabase-migration-testing.md) - 完整測試指南
- [測試 Fixtures 指南](./testing/test-fixtures.md) - Fixture 使用說明
- [清理機制指南](./testing/cleanup-mechanism.md) - 測試資料清理
- [SQL 整合測試](./testing/sql-integration-tests.md) - SQL 初始化測試
- [測試資料隔離](./testing/test-data-isolation.md) - 測試資料隔離機制

### 🌍 多語言文件

- [中文版 README](./README_zh.md) - 繁體中文說明
- [Docker 中文指南](./README_DOCKER.md) - Docker 中文說明

---

## 📂 文件結構

```
docs/
├── README.md                          # 本文件（索引）
├── QUICKSTART.md                      # 快速開始
├── FINAL_VERIFICATION_CHECKLIST.md   # 驗證清單
│
├── setup/                             # 設定相關
│   ├── ENV_SETUP_GUIDE.md
│   ├── ENV_STRUCTURE_SUMMARY.md
│   ├── ENV_MIGRATION_SUMMARY.md
│   └── OAUTH_SETUP_GUIDE.md
│
├── docker/                            # Docker 相關
│   ├── DOCKER_GUIDE.md
│   ├── DOCKER_ARCHITECTURE.md
│   └── DOCKER_COMPARISON.md
│
├── deployment/                        # 部署相關
│   ├── DEPLOYMENT.md
│   └── DEPLOYMENT_CHECKLIST.md
│
└── testing/                           # 測試相關
    ├── supabase-migration-testing.md
    ├── test-fixtures.md
    ├── cleanup-mechanism.md
    ├── sql-integration-tests.md
    └── test-data-isolation.md
```

---

## 🎯 依情境選擇文件

### 我是新手，想快速開始

1. [快速開始指南](./QUICKSTART.md)
2. [環境變數設定指南](./setup/ENV_SETUP_GUIDE.md)
3. [使用者指南](./USER_GUIDE.md)

### 我要設定開發環境

1. [Docker 使用指南](./docker/DOCKER_GUIDE.md)
2. [環境變數設定指南](./setup/ENV_SETUP_GUIDE.md)
3. [OAuth 設定指南](./setup/OAUTH_SETUP_GUIDE.md)

### 我要部署到正式環境

1. [部署檢查清單](./deployment/DEPLOYMENT_CHECKLIST.md)
2. [部署指南](./deployment/DEPLOYMENT.md)
3. [Docker 環境比較](./docker/DOCKER_COMPARISON.md)

### 我要了解架構

1. [開發者指南](./DEVELOPER_GUIDE.md)
2. [專案概覽](./PROJECT_OVERVIEW.md)
3. [Docker 架構說明](./docker/DOCKER_ARCHITECTURE.md)

### 我要寫測試

1. [Supabase 遷移測試](./testing/supabase-migration-testing.md)
2. [測試 Fixtures 指南](./testing/test-fixtures.md)
3. [清理機制指南](./testing/cleanup-mechanism.md)

---

## 🔗 外部資源

- [Supabase 文件](https://supabase.com/docs)
- [Discord.py 文件](https://discordpy.readthedocs.io/)
- [FastAPI 文件](https://fastapi.tiangolo.com/)
- [Next.js 文件](https://nextjs.org/docs)
- [Docker 文件](https://docs.docker.com/)

---

最後更新：2024-01-01
