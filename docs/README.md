# Tech News Agent - 文件索引

## 📚 快速導航

### 🚀 快速開始

- **[快速開始指南](./QUICKSTART.md)** - 最快速的上手方式
- **[環境變數設定指南](./setup/ENV_SETUP_GUIDE.md)** - 完整的環境變數說明
- **[最終驗證清單](./FINAL_VERIFICATION_CHECKLIST.md)** - 功能驗證檢查清單

### 📖 使用者指南

- **[使用者指南](./USER_GUIDE.md)** - Discord 指令與 Web 介面完整說明
- **[手動觸發 Scheduler](./MANUAL_SCHEDULER_TRIGGER.md)** - 隨時抓取新文章
- **[公開 Bot 設定](./PUBLIC_BOT_SETUP.md)** - 將 Bot 設為公開並支援 DM 通知

### 👨‍💻 開發者指南

- **[開發者指南](./DEVELOPER_GUIDE.md)** - 架構與 API 參考
- **[專案概覽](./PROJECT_OVERVIEW.md)** - 完整的系統文件
- **[速率限制指南](./RATE_LIMIT_GUIDE.md)** - API 速率限制說明
- **[檔案組織](./FILE_ORGANIZATION.md)** - 專案結構說明

### ⚙️ 設定指南

- **[環境變數設定指南](./setup/ENV_SETUP_GUIDE.md)** - 完整的環境變數說明
- **[環境變數結構總結](./setup/ENV_STRUCTURE_SUMMARY.md)** - 環境變數架構說明
- **[OAuth 設定指南](./setup/OAUTH_SETUP_GUIDE.md)** - Discord OAuth 設定

### 🐳 Docker 文件

- **[Docker 使用指南](./docker/DOCKER_GUIDE.md)** - Docker Compose 完整說明
- **[Docker 架構說明](./docker/DOCKER_ARCHITECTURE.md)** - 開發與正式環境架構
- **[Docker 環境比較](./docker/DOCKER_COMPARISON.md)** - 開發 vs 正式環境差異
- **[Docker 中文指南](./README_DOCKER.md)** - Docker 設定說明（中文）

### 🚢 部署文件

- **[部署指南](./deployment/DEPLOYMENT.md)** - 完整部署流程
- **[部署檢查清單](./deployment/DEPLOYMENT_CHECKLIST.md)** - 部署前檢查項目
- **[手動觸發部署檢查清單](./deployment/DEPLOYMENT_CHECKLIST_MANUAL_TRIGGER.md)** - 手動觸發功能部署檢查

### 🧪 測試文件

- **[Supabase 遷移測試](./testing/supabase-migration-testing.md)** - 完整測試指南
- **[測試 Fixtures 指南](./testing/test-fixtures.md)** - Fixture 使用說明
- **[清理機制指南](./testing/cleanup-mechanism.md)** - 測試資料清理
- **[SQL 整合測試](./testing/sql-integration-tests.md)** - SQL 初始化測試
- **[測試資料隔離](./testing/test-data-isolation.md)** - 測試資料隔離機制
- **[Property 24 測試](./testing/property-24-tests.md)** - Onboarding UI 條件顯示測試

### 🛠️ 開發記錄

- **[CI 優化記錄](./development/CI_OPTIMIZATION.md)** - CI/CD 優化歷程
- **[實作總結](./development/IMPLEMENTATION_SUMMARY.md)** - 功能實作總結
- **[測試分析](./development/TEST_ANALYSIS.md)** - 測試覆蓋率分析
- **[規格完成總結](./development/SPEC_COMPLETION_SUMMARY.md)** - 規格實作記錄
- **[Auth Schema 修復](./development/BUGFIX_AUTH_SCHEMA.md)** - 認證架構修復記錄
- **[資料庫遷移指南](./development/MIGRATIONS.md)** - 資料庫遷移完整說明

### 🌍 多語言文件

- **[中文版 README](./README_zh.md)** - 繁體中文說明
- **[English README](../README.md)** - English documentation

---

## 📂 文件結構

```
docs/
├── README.md                          # 本文件（索引）
├── QUICKSTART.md                      # 快速開始
├── FINAL_VERIFICATION_CHECKLIST.md   # 驗證清單
├── USER_GUIDE.md                      # 使用者指南
├── DEVELOPER_GUIDE.md                 # 開發者指南
├── PROJECT_OVERVIEW.md                # 專案概覽
├── MANUAL_SCHEDULER_TRIGGER.md        # 手動觸發 Scheduler
├── PUBLIC_BOT_SETUP.md                # 公開 Bot 設定
├── RATE_LIMIT_GUIDE.md                # 速率限制指南
├── FILE_ORGANIZATION.md               # 檔案組織說明
│
├── setup/                             # 設定相關
│   ├── ENV_SETUP_GUIDE.md            # 環境變數設定指南
│   ├── ENV_STRUCTURE_SUMMARY.md      # 環境變數結構
│   └── OAUTH_SETUP_GUIDE.md          # OAuth 設定
│
├── docker/                            # Docker 相關
│   ├── DOCKER_GUIDE.md               # Docker 使用指南
│   ├── DOCKER_ARCHITECTURE.md        # Docker 架構
│   └── DOCKER_COMPARISON.md          # 環境比較
│
├── deployment/                        # 部署相關
│   ├── DEPLOYMENT.md                 # 部署指南
│   ├── DEPLOYMENT_CHECKLIST.md       # 部署檢查清單
│   └── DEPLOYMENT_CHECKLIST_MANUAL_TRIGGER.md
│
├── testing/                           # 測試相關
│   ├── supabase-migration-testing.md # Supabase 測試
│   ├── test-fixtures.md              # Test Fixtures
│   ├── cleanup-mechanism.md          # 清理機制
│   ├── sql-integration-tests.md      # SQL 測試
│   ├── test-data-isolation.md        # 資料隔離
│   └── property-24-tests.md          # Property 測試
│
├── development/                       # 開發記錄
│   ├── CI_OPTIMIZATION.md            # CI 優化
│   ├── IMPLEMENTATION_SUMMARY.md     # 實作總結
│   ├── TEST_ANALYSIS.md              # 測試分析
│   ├── SPEC_COMPLETION_SUMMARY.md    # 規格完成
│   ├── BUGFIX_AUTH_SCHEMA.md         # Bug 修復
│   └── MIGRATIONS.md                 # 資料庫遷移
│
├── README_zh.md                       # 中文版 README
└── README_DOCKER.md                   # Docker 中文指南
```

---

## 🎯 依情境選擇文件

### 我是新手，想快速開始

1. **[快速開始指南](./QUICKSTART.md)** - 5 分鐘內啟動專案
2. **[環境變數設定指南](./setup/ENV_SETUP_GUIDE.md)** - 設定所有必要的環境變數
3. **[使用者指南](./USER_GUIDE.md)** - 學習如何使用 Discord 指令和 Web 介面

### 我要設定開發環境

1. **[Docker 使用指南](./docker/DOCKER_GUIDE.md)** - 使用 Docker Compose 快速啟動
2. **[環境變數設定指南](./setup/ENV_SETUP_GUIDE.md)** - 配置開發環境變數
3. **[OAuth 設定指南](./setup/OAUTH_SETUP_GUIDE.md)** - 設定 Discord OAuth 登入

### 我要部署到正式環境

1. **[部署檢查清單](./deployment/DEPLOYMENT_CHECKLIST.md)** - 部署前必須檢查的項目
2. **[部署指南](./deployment/DEPLOYMENT.md)** - 完整的部署步驟
3. **[Docker 環境比較](./docker/DOCKER_COMPARISON.md)** - 了解開發與正式環境的差異

### 我要了解系統架構

1. **[專案概覽](./PROJECT_OVERVIEW.md)** - 完整的系統架構說明
2. **[開發者指南](./DEVELOPER_GUIDE.md)** - API 參考與開發指南
3. **[Docker 架構說明](./docker/DOCKER_ARCHITECTURE.md)** - 容器化架構設計

### 我要寫測試

1. **[Supabase 遷移測試](./testing/supabase-migration-testing.md)** - 資料庫測試策略
2. **[測試 Fixtures 指南](./testing/test-fixtures.md)** - 如何使用測試 fixtures
3. **[清理機制指南](./testing/cleanup-mechanism.md)** - 測試資料清理機制

### 我要設定公開 Bot

1. **[公開 Bot 設定](./PUBLIC_BOT_SETUP.md)** - 將 Bot 設為公開
2. **[手動觸發 Scheduler](./MANUAL_SCHEDULER_TRIGGER.md)** - 設定手動觸發功能
3. **[使用者指南](./USER_GUIDE.md)** - 了解所有可用功能

---

## 🔗 外部資源

### 技術文件

- **[Supabase 文件](https://supabase.com/docs)** - 資料庫與認證
- **[Discord.py 文件](https://discordpy.readthedocs.io/)** - Discord Bot 開發
- **[FastAPI 文件](https://fastapi.tiangolo.com/)** - 後端框架
- **[Next.js 文件](https://nextjs.org/docs)** - 前端框架
- **[Docker 文件](https://docs.docker.com/)** - 容器化部署

### 工具與服務

- **[Groq Cloud](https://console.groq.com)** - AI 模型 API
- **[Discord Developer Portal](https://discord.com/developers/applications)** - Bot 設定
- **[shadcn/ui](https://ui.shadcn.com)** - UI 元件庫

---

**最後更新：2026-04-05**

有問題或建議？歡迎在 [GitHub Issues](https://github.com/yourusername/tech-news-agent/issues) 提出！
