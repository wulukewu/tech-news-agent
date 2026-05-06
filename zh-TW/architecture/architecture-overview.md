# 架構概覽

> 最後更新：2026-05-04

---

## 高層次概覽

技術新聞代理是一個多平台、AI 驅動的新聞策展系統。它結合了 FastAPI 後端、Next.js 網路儀表板和 Discord 機器人——所有這些都由 Supabase (PostgreSQL + pgvector) 和 Groq LLM 提供支援。

```
┌─────────────────┐     ┌──────────────────────┐     ┌─────────────────┐
│   Next.js 網路   │────▶│   FastAPI 後端        │────▶│    Supabase     │
│   儀表板        │     │   + Discord 機器人    │     │   PostgreSQL    │
│   (i18n EN/ZH)  │     │   + QA 代理         │     │   + pgvector    │
└─────────────────┘     └──────────────────────┘     └─────────────────┘
        │                         │                           │
        ▼                         ▼                           ▼
  Discord OAuth            Groq LLM API              向量搜尋
  React Query              APScheduler               對話儲存
  功能切片                   動態排程器                 知識圖譜
```

---

## 技術棧

| 層次     | 技術                                                    |
|----------|---------------------------------------------------------|
| **前端** | Next.js 14 (App Router), React 18, TypeScript, Tailwind CSS, shadcn/ui |
| **狀態 / 資料提取** | React Query, Split Context 模式                     |
| **國際化** | next-intl (EN / ZH)                                     |
| **後端** | FastAPI, Python 3.11+                                     |
| **Discord 機器人** | discord.py 2.4+                                       |
| **排程器** | APScheduler 3.10+                                       |
| **資料庫** | Supabase (PostgreSQL + pgvector)                        |
| **AI / LLM** | Groq Cloud — Llama 3.1 8B (評分), Llama 3.3 70B (摘要) |
| **身份驗證** | Discord OAuth (網頁登入), JWT                           |
| **測試** | pytest, Hypothesis, Jest, Playwright                    |

---

## 核心架構模式

### 1. 儲存庫模式 (`app/repositories/`)

將所有資料庫存取抽象化為型別化介面。每個實體（用戶、文章、動態消息、閱讀清單等）都有專用的儲存庫。儲存庫處理 CRUD、軟刪除、審計日誌和業務規則驗證——使 SQL 脫離服務層。

### 2. 帶 Mixin 模式的服務層 (`app/services/`)

約 50 個服務文件實現業務邏輯。大型服務類別由位於 `app/services/_mixins/`（文章、動態消息、閱讀清單、通知、用戶）的專注 Mixin 組成。這使得各個文件保持小巧，同時允許豐富的服務物件。

```
SupabaseService
  ├── ArticleMixin       (提取、評分、摘要)
  ├── FeedMixin          (訂閱、取消訂閱、驗證)
  ├── ReadingListMixin   (儲存、評分、推薦)
  ├── NotificationMixin  (發送 DM、勿擾時段、歷史記錄)
  └── UserMixin          (個人資料、偏好設定、統計資料)
```

### 3. QA 代理子系統 (`app/qa_agent/`)

一個自包含的子系統，為用戶訂閱的文章提供對話式 AI。組件：

| 組件                  | 職責                                     |
|-----------------------|------------------------------------------|
| `qa_agent_controller.py` | 入口點；協調完整的 QA 管道              |
| `query_processor.py`  | 解析和分類傳入問題                       |
| `retrieval_engine.py` | 透過 pgvector 嵌入進行向量搜尋           |
| `response_generator.py` | 調用 Groq LLM 生成答案                   |
| `conversation_manager.py` | 持久化多輪聊天歷史記錄                   |
| `user_profile_manager.py` | 從評分和歷史記錄中學習偏好設定           |
| `security_manager.py` | 強制執行每個用戶的資料隔離                 |
| `performance_monitor.py` | 追蹤延遲和令牌使用量                     |

子模組透過更高級別的功能擴展 QA 代理：

- `knowledge_graph/` — 文章依賴和概念連結
- `intelligent_reminder/` — 上下文感知閱讀提醒
- `weekly_insights/` — 趨勢檢測和主題聚類
- `proactive_learning/` — 自適應內容推薦
- `learning_path/` — 技能樹和目標追蹤

### 4. 特性切片前端 (`frontend/features/`)

前端程式碼按功能域而非文件類型組織：

```
frontend/features/
├── articles/
├── ai-analysis/
├── notifications/
├── recommendations/
├── subscriptions/
└── system-monitor/
```

每個特性切片擁有其組件、Hooks 和 API 調用。共享 UI 原語位於 `frontend/components/` (shadcn/ui)。

### 5. 分割上下文模式 (`frontend/contexts/`)

React 上下文按關注點（身份驗證、用戶、主題）分割，以最小化重新渲染範圍。伺服器狀態（文章、動態消息、閱讀清單）由 React Query 管理，具有可配置的過時/快取時間。

### 6. 集中式錯誤處理和日誌記錄 (`app/core/`)

- `app/core/exceptions.py` — 帶有 `ErrorCode` 列舉的型別化 `AppException` 階層
- `app/core/logger.py` — 帶有請求作用域上下文（請求 ID、用戶 ID）的結構化 JSON 日誌記錄，透過 `contextvars`
- FastAPI 異常處理程序將 `AppException` 映射到一致的 JSON 錯誤回應

---

## 資料流

### API 請求流

```
瀏覽器 / Discord 機器人
  → FastAPI 路由
  → 身份驗證中介軟體 (JWT 驗證)
  → 服務層 (業務邏輯、Mixin 組成)
  → 儲存庫層 (Supabase 查詢)
  → 標準化 JSON 回應
```

### 通知流

```
APScheduler (每個用戶動態排程)
  → dynamic_scheduler.py 評估每個用戶的時區、頻率、勿擾時段
  → NotificationMixin 提取相關文章
  → LLM 生成個人化摘要 (Llama 3.3 70B)
  → discord.py 發送 DM
  → 通知歷史記錄在 Supabase 中
```

### QA / 對話流

```
用戶問題 (網頁或 Discord)
  → qa_agent_controller
  → query_processor (分類意圖)
  → retrieval_engine (pgvector 相似度搜尋)
  → response_generator (帶有檢索上下文的 Groq LLM)
  → conversation_manager (將輪次持久化到 Supabase)
  → 回應返回給用戶
```

---

## 多租戶設計

每個面向用戶的資源都透過 `user_id` 範圍限定：

- **訂閱** — 每個用戶管理自己的 RSS 動態消息清單 (`user_subscriptions` 表)
- **閱讀清單** — 每個用戶私有；評分饋送推薦引擎
- **通知偏好設定** — 每個用戶的頻率、發送時間、時區、勿擾時段
- **對話** — 聊天歷史記錄每個用戶獨立隔離；`security_manager.py` 在 QA 層強制執行此操作
- **動態排程器** — `dynamic_scheduler.py` 在 APScheduler 中為每個用戶維護一個作業，尊重每個用戶從其偏好設定中派生的排程

沒有共享的全局動態消息或閱讀清單。資料隔離在儲存庫層（所有查詢都按 `user_id` 篩選）和 QA 代理的 `security_manager` 中強制執行。

---

## 關鍵設計決策

**基於 Mixin 的服務組合優於繼承鏈** — 有約 50 個服務關注點，深層繼承變得難以管理。Mixin 允許 `SupabaseService` 只組合其需要的功能，同時保持每個 Mixin 獨立可測試。

**pgvector 用於語義搜尋** — 將文章嵌入直接儲存在 Supabase (PostgreSQL) 中，避免了單獨的向量資料庫。這簡化了基礎設施，同時支援 QA 檢索引擎和推薦的相似度搜尋。

**QA 代理作為自包含子系統** — 將對話式 AI 隔離到 `app/qa_agent/` 中，擁有自己的控制器、檢索和個人資料管理，意味著它可以在不耦合關注點的情況下獨立於核心 CRUD API 演進。

**每個用戶動態排程器** — 單一的全局 cron 會在不同時區的用戶錯誤時間發送通知。`dynamic_scheduler.py` 在 APScheduler 中為每個用戶註冊單獨的作業，每個作業都有其從用戶偏好設定中派生的排程。

**特性切片前端** — 按功能分組（而不是按 `components/`、`hooks/`、`utils/`）意味著一個功能的所有程式碼都位於同一位置，減少了跨切變更的認知開銷。

**Discord OAuth 作為唯一的身份提供者** — 由於 Discord 機器人是第一類客戶端，使用 Discord OAuth 進行網頁登入意味著在兩個介面上都有一個用戶身份，簡化了用戶模型並消除了單獨的註冊流程。
