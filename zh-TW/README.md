# 技術新聞代理 — 文件

> 📖 [Back to English Version](en/README.md)

技術新聞代理專案的完整文件。請使用以下各節進行導覽。

---

## 🚀 快速入門

| | |
|---|---|
| [快速入門](guides/quick-start.md) | 在數分鐘內啟動並運行 |
| [環境設定](setup/env-setup-guide.md) | 設定 `.env` 和憑證 |
| [OAuth 設定](setup/oauth-setup-guide.md) | Discord OAuth 設定 |
| [Docker 指南](docker/docker-guide.md) | 使用 Docker Compose 運行 |
| [用戶指南](guides/user-guide.md) | 終端用戶功能導覽 |

---

## 🏗️ 架構與設計

| | |
|---|---|
| [架構概覽](architecture/architecture-overview.md) | 系統設計、組件、資料流 |
| [專案概覽](architecture/project-overview.md) | 高層次專案摘要 |
| [通知鎖定機制](architecture/notification-lock-mechanism.md) | 用於通知的分散式鎖定 |
| [API 契約](api/api-contracts.md) | 完整的 REST API 規範 |
| [智能對話端點](api/smart-conversation-endpoints.md) | 對話與 QA API 詳細資訊 |

---

## ⚙️ 後端

| | |
|---|---|
| [後端概覽](backend/README.md) | 所有後端文件的索引 |
| [機器人 / Discord Cogs](backend/bot/README.md) | Discord 機器人架構與 Cog 參考 |
| [核心層](backend/core/README.md) | 配置、錯誤、日誌記錄器、驗證器 |
| [服務](backend/services/README.md) | 服務層、排程器、速率限制 |
| [QA 代理](backend/qa-agent/README.md) | 對話式 AI 子系統 |
| [儲存庫](backend/repositories/README.md) | 資料存取層 |
| [通知](backend/notifications/README.md) | 通知系統內部 |
| [遷移](backend/migrations/README.md) | 資料庫遷移指南 |
| [實作細節](backend/implementation/README.md) | 特定功能實作 |
| [測試](backend/tests/README.md) | 測試結構與覆蓋率 |
| [故障排除](backend/troubleshooting/README.md) | 後端特定問題 |

---

## 🎨 前端

| | |
|---|---|
| [前端概覽](frontend/README.md) | 所有前端文件的索引 |
| [i18n 指南](frontend/i18n-guide.md) | 國際化 (EN/ZH) |
| [設計代幣](frontend/design-tokens.md) | 顏色、排版、間距系統 |
| [ESLint i18n 規則](frontend/eslint-i18n-rules.md) | 翻譯的 Linting 規則 |
| [元件](frontend/components/README.md) | UI 元件文件 |
| [上下文](frontend/contexts/README.md) | React 上下文提供者 |
| [函式庫 / API 客戶端](frontend/lib/README.md) | API 客戶端、Hooks、實用工具 |
| [測試](frontend/tests/README.md) | 前端測試結構 |

---

## 🚢 部署

| | |
|---|---|
| [部署指南](deployment/deployment-guide.md) | 完整部署教學 |
| [部署清單](deployment/deployment-checklist.md) | 部署前清單 |
| [回滾程序](deployment/rollback-procedures.md) | 如何回滾發布 |
| [Netlify 前端](deployment/netlify-frontend.md) | 部署前端到 Netlify |
| [Render 後端](deployment/render-deployment.md) | 部署後端到 Render |
| [公開機器人設定](deployment/public-bot-setup.md) | 用於公開伺服器的 Discord 機器人 |
| [所有部署文件](deployment/README.md) | 完整部署索引 |

---

## 💻 開發

| | |
|---|---|
| [開發人員指南](development/developer-guide.md) | 設定、工作流程、慣例 |
| [開發工作流程](development/development-workflows.md) | 日常開發流程 |
| [程式碼品質](development/code-quality.md) | Linting、格式化、標準 |
| [Pre-commit Hooks](development/pre-commit-hooks.md) | 提交時自動檢查 |
| [重構指南](development/refactoring-migration-guide.md) | 大規模重構模式 |
| [所有開發文件](development/README.md) | 完整開發索引 |

---

## 🧪 測試

| | |
|---|---|
| [測試指南](testing/testing-guide.md) | 測試策略與如何運行測試 |
| [測試夾具](testing/test-fixtures.md) | 共享夾具與工廠 |
| [測試數據隔離](testing/test-data-isolation.md) | 保持測試獨立 |
| [所有測試文件](testing/README.md) | 完整測試索引 |

---

## 🔧 設定與配置

| | |
|---|---|
| [環境變數](setup/env-setup-guide.md) | 所有環境變數解釋 |
| [快速環境設定](setup/quick-env-setup.md) | 本地開發的最小設定 |
| [所有設定文件](setup/README.md) | 完整設定索引 |

---

## 🗄️ 資料庫遷移

| | |
|---|---|
| [遷移指南](migrations/migration-guide.md) | 如何運行與編寫遷移 |
| [遷移 009 指南](migrations/migration-009-guide.md) | 特定遷移參考 |
| [腳本參考](scripts/README.md) | 遷移與實用腳本 |

---

## ✨ 功能與改進

| | |
|---|---|
| [功能](features/README.md) | 功能設計文件 |
| [改進](improvements/README.md) | 路線圖與改進建議 |
| [UX 改進](ux-improvements/README.md) | UI/UX 變更記錄 |
| [實作說明](implementation/README.md) | 功能實作摘要 |

---

## 🚨 修正與故障排除

| | |
|---|---|
| [故障排除指南](troubleshooting/troubleshooting-guide.md) | 常見問題與解決方案 |
| [已知修正](fixes/README.md) | 文件化錯誤修正 |

---

## 📦 存檔

歷史開發記錄（任務完成情況、CI 狀態快照、修正摘要）。

→ [瀏覽存檔](archive/README.md)

---

## 📁 目錄結構

```
docs/
├── api/                  API 契約與端點規範
├── architecture/         系統架構與設計決策
├── backend/              後端文件 (機器人、核心、服務、QA 代理等)
├── ci/                   CI/CD 配置與指南
├── deployment/           部署指南 (Netlify, Render, Docker 等)
├── development/          開發人員指南、工作流程、程式碼品質
├── docker/               Docker 特定文件
├── features/             功能設計文件
├── fixes/                關鍵錯誤修正文件
├── frontend/             前端文件 (i18n、元件、函式庫等)
├── guides/               面向用戶的指南與快速入門
├── implementation/       功能實作摘要
├── improvements/         改進建議與路線圖
├── migrations/           資料庫遷移指南
├── scripts/              腳本使用文件
├── setup/                環境與配置設定
├── testing/              測試策略與指南
├── troubleshooting/      故障排除指南
├── ui-improvements/      UI 變更記錄
├── ux-improvements/      UX 變更記錄
└── archive/              歷史任務/CI/修正記錄
```
