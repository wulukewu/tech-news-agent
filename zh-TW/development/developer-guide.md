# 開發人員指南

## 目錄

1. [先決條件與設定](#1-先決條件與設定)
2. [專案結構](#2-專案結構)
3. [開發工作流程](#3-開發工作流程)
4. [程式碼品質](#4-程式碼品質)
5. [測試](#5-測試)
6. [新增功能](#6-新增功能)
7. [關鍵慣例](#7-關鍵慣例)

---

## 1. 先決條件與設定

### 需求

- Python 3.11+
- Node.js 18+
- Docker & Docker Compose (推薦)
- 啟用 pgvector 的 Supabase 專案
- Groq API 密鑰
- Discord 應用程式 (機器人 Token + OAuth 憑證)

### 初始設定

```bash
# 克隆並進入倉庫
git clone https://github.com/yourusername/tech-news-agent.git
cd tech-news-agent

# 複製並填寫環境變數
cp .env.example .env
# 編輯 .env — 請參閱下面的環境變數部分

# 初始化資料庫
# 在 Supabase SQL 編輯器中執行 backend/scripts/init_supabase.sql
```

### 環境變數

| 變數                             | 必需 | 描述                           |
|----------------------------------|------|--------------------------------|
| `SUPABASE_URL`                   | ✅   | Supabase 專案 URL              |
| `SUPABASE_KEY`                   | ✅   | Supabase 服務角色密鑰          |
| `GROQ_API_KEY`                   | ✅   | Groq API 密鑰                  |
| `JWT_SECRET_KEY`                 | ✅   | JWT 簽名密鑰 (`openssl rand -hex 32`) |
| `JWT_ALGORITHM`                  | ✅   | `HS256`                        |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES`| ✅   | 例如 `30`                      |
| `DISCORD_CLIENT_ID`              | ✅   | Discord OAuth 用戶端 ID        |
| `DISCORD_CLIENT_SECRET`          | ✅   | Discord OAuth 用戶端密鑰       |
| `DISCORD_REDIRECT_URI`           | ✅   | 例如 `http://localhost:3000/auth/callback` |
| `NEXT_PUBLIC_API_URL`            | ✅   | 例如 `http://localhost:8000`   |
| `DISCORD_TOKEN`                  | 可選 | 機器人 Token (Discord 機器人必需) |
| `DISCORD_CHANNEL_ID`             | 可選 | 機器人公告的預設頻道           |
| `SCHEDULER_CRON`                 | 可選 | 預設: `0 */6 * * *`            |
| `SCHEDULER_TIMEZONE`             | 可選 | 預設: `Asia/Taipei`            |
| `TIMEZONE`                       | 可選 | 預設: `Asia/Taipei`            |
| `RSS_FETCH_DAYS`                 | 可選 | 抓取歷史天數 (預設: `7`)       |
| `LOG_LEVEL`                      | 可選 | 預設: `INFO`                   |

---

## 2. 專案結構

```
tech-news-agent/
├── backend/
│   ├── app/
│   │   ├── api/               # REST API 端點 (FastAPI 路由)
│   │   │   ├── auth.py
│   │   │   ├── articles.py
│   │   │   ├── feeds.py
│   │   │   ├── reading_list.py
│   │   │   ├── qa.py
│   │   │   ├── conversations/
│   │   │   ├── notifications/
│   │   │   ├── learning_path/
│   │   │   └── ...
│   │   ├── bot/
│   │   │   ├── cogs/          # 13 個 Discord 機器人命令 cogs
│   │   │   └── client.py
│   │   ├── services/          # 約 50 個服務文件 (mixin 模式)
│   │   │   └── _mixins/       # article, feed, reading_list, notification, user
│   │   ├── qa_agent/          # QA 子系統 (向量搜尋、對話、學習)
│   │   ├── core/              # 配置、異常、日誌記錄器、驗證器
│   │   ├── repositories/      # 資料存取層 (Supabase 查詢)
│   │   ├── schemas/           # Pydantic 模型
│   │   └── tasks/             # APScheduler 背景作業
│   ├── scripts/               # 資料庫初始化、遷移、實用工具
│   ├── tests/                 # pytest 測試套件
│   └── requirements.txt
│
├── frontend/
│   ├── app/                   # Next.js 14 App Router 頁面
│   │   ├── (public)/          # 未經身份驗證的路由
│   │   └── app/               # 經身份驗證的路由
│   ├── features/              # 特性切片組件
│   ├── components/            # 共享 UI (shadcn/ui)
│   ├── lib/                   # API 客戶端、Hooks、實用工具
│   ├── locales/               # i18n 字串 (EN/ZH)
│   └── package.json
│
├── docs/                      # 所有文件
├── scripts/                   # 開發、CI、遷移腳本
├── docker-compose.yml         # 開發
├── docker-compose.prod.yml    # 生產
└── Makefile
```

### 後端層次職責

| 層次       | 路徑                 | 職責                          |
|------------|----------------------|-------------------------------|
| API        | `app/api/`           | HTTP 請求處理、身份驗證、回應塑形 |
| 機器人     | `app/bot/cogs/`      | Discord 斜線命令與互動         |
| 服務       | `app/services/`      | 業務邏輯、協調                  |
| 儲存庫     | `app/repositories/`  | 所有 Supabase/資料庫查詢       |
| Schema     | `app/schemas/`       | Pydantic 請求/回應模型         |
| 任務       | `app/tasks/`         | 排程背景作業                  |
| 核心       | `app/core/`          | 配置、日誌記錄、共享異常         |

---

## 3. 開發工作流程

### 選項 A: Docker Compose (推薦)

```bash
# 開發 (熱重載)
make dev
# 或
docker-compose up -d

# 查看日誌
docker-compose logs -f backend
docker-compose logs -f frontend

# 停止
docker-compose down
```

存取方式：
- 網頁: http://localhost:3000
- API: http://localhost:8000
- API 文件: http://localhost:8000/docs

### 選項 B: 本地開發

**後端：**

```bash
cd backend
pip install -r requirements.txt
python -m app.main
```

**前端** (另一個終端機)：

```bash
cd frontend
npm install
npm run dev
```

### Pre-commit Hooks

克隆後安裝一次：

```bash
pip install pre-commit
pre-commit install
```

Hooks 在 `git commit` 時自動運行：
- `black` — Python 格式化
- `ruff` — Python Linting
- `prettier` — TypeScript/CSS 格式化
- `eslint` — TypeScript Linting
- 翻譯驗證 — 確保 EN/ZH 地區設定鍵同步

---

## 4. 程式碼品質

### 後端工具

| 工具     | 目的               | 命令            |
|----------|--------------------|-----------------|
| `ruff`   | Linting + 導入排序 | `ruff check app/` |
| `black`  | 格式化             | `black app/`    |
| `mypy`   | 靜態型別檢查       | `mypy app/`     |

### 前端工具

| 工具       | 目的     | 命令                   |
|------------|----------|------------------------|
| `eslint`   | Linting  | `npm run lint`         |
| `prettier` | 格式化   | `npm run format`       |
| TypeScript | 型別檢查 | `npm run type-check`   |

### CI 腳本

```bash
# 自動修正格式化和 Linting 問題
./scripts/ci-fix.sh

# 完整的 CI 檢查 (模擬 GitHub Actions — 在推送前運行)
./scripts/ci-local-test.sh
```

在開啟 PR 之前，請務必運行 `./scripts/ci-local-test.sh`。

### Python 程式碼標準

- 所有函數簽名上使用型別提示
- 在公共函數上編寫 Google 風格的文檔字串
- 遵循 PEP 8 (由 ruff/black 強制執行)
- 明確處理異常 — 絕不默默吞噬錯誤

```python
async def get_user_articles(user_id: str, limit: int = 20) -> list[ArticleSchema]:
    """為用戶訂閱的動態消息獲取文章。

    Args:
        user_id: 用戶的 UUID 字串。
        limit: 返回的最大文章數量。

    Returns:
        按 published_at 降序排列的文章 Schema 列表。

    Raises:
        RepositoryError: 如果資料庫查詢失敗。
    """
    return await self.article_repo.get_for_user(user_id, limit=limit)
```

---

## 5. 測試

### 後端

```bash
cd backend

# 運行所有測試
pytest -v

# 帶覆蓋率報告
pytest --cov=app --cov-report=html

# 基於屬性的測試 (Hypothesis profiles)
HYPOTHESIS_PROFILE=dev pytest tests/test_database_properties.py -v   # 10 個範例 (快速)
HYPOTHESIS_PROFILE=ci  pytest tests/test_database_properties.py -v   # 100 個範例
```

測試結構：

```
backend/tests/
├── conftest.py
├── test_config.py
├── test_database_properties.py   # Hypothesis 屬性測試
├── bot/
│   ├── utils/test_validators.py
│   └── test_performance.py
└── integration/
    └── test_multi_tenant_workflow.py
```

測試類型：
- **單元測試**: 個別函數和驗證器
- **基於屬性的測試**: Hypothesis 用於不變量 (例如，評分始終為 1–5)
- **整合測試**: 跨服務 + 儲存庫層的完整用戶旅程
- **性能測試**: 關鍵路徑的響應時間斷言

### 前端

```bash
cd frontend

# 單元測試 (vitest)
npm test

# 帶覆蓋率
npm run test:coverage

# E2E 測試 (Playwright)
npm run test:e2e
```

---

## 6. 新增功能

### A. 新增 API 端點

1. 在 `backend/app/api/` 中創建路由文件 (或添加到現有文件)：

```python
# backend/app/api/my_feature.py
from fastapi import APIRouter, Depends
from app.core.auth import get_current_user
from app.schemas.my_feature import MyFeatureResponse
from app.services.my_feature_service import MyFeatureService

router = APIRouter(prefix="/api/my-feature", tags=["my-feature"])

@router.get("/", response_model=MyFeatureResponse)
async def get_my_feature(current_user=Depends(get_current_user)):
    service = MyFeatureService()
    return await service.get(current_user["id"])
```

2. 在 `backend/app/main.py` 中註冊路由：

```python
from app.api.my_feature import router as my_feature_router
app.include_router(my_feature_router)
```

3. 在 `backend/app/schemas/my_feature.py` 中添加 Pydantic Schema。
4. 在 `backend/app/repositories/` 中添加儲存庫方法。
5. 在 `backend/app/services/` 中添加服務邏輯。
6. 在 `backend/tests/` 中編寫測試。

### B. 新增 Discord 機器人命令

1. 在 `backend/app/bot/cogs/` 中創建或添加到一個 cog：

```python
# backend/app/bot/cogs/my_commands.py
import discord
from discord.ext import commands
from discord import app_commands

class MyCommands(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="my_command", description="執行有用的操作")
    async def my_command(self, interaction: discord.Interaction):
        await interaction.response.defer()
        # 業務邏輯在此
        await interaction.followup.send("完成！")

async def setup(bot: commands.Bot):
    await bot.add_cog(MyCommands(bot))
```

2. 在 `backend/app/bot/client.py` 的 cog 加載部分註冊 cog。

3. 對於任何可能需要超過 3 秒的操作，請使用 `await interaction.response.defer()`。

### C. 新增前端頁面

1. 在 `frontend/app/app/my-page/` 下創建頁面目錄：

```
frontend/app/app/my-page/
├── page.tsx        # 頁面組件
└── loading.tsx     # 可選的加載 UI
```

2. 在 `frontend/features/my-feature/` 中添加功能組件：

```typescript
// frontend/features/my-feature/components/MyFeatureCard.tsx
interface MyFeatureCardProps {
  data: MyFeatureData;
}

export function MyFeatureCard({ data }: MyFeatureCardProps) {
  return <div>{data.title}</div>;
}
```

3. 在 `frontend/lib/api/` 中添加 API 調用，並在 `frontend/lib/hooks/` 中添加 React Query Hooks。

4. 將 i18n 字串同時添加到 `frontend/locales/en.json` 和 `frontend/locales/zh.json` (pre-commit hook 將驗證它們保持同步)。

---

## 7. 關鍵慣例

### Git 提交

使用 [Conventional Commits](https://www.conventionalcommits.org/)：

```
<類型>(<範圍>): <主旨>

[可選內容]

[可選腳註]
```

類型: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

範例：
```
feat(api): 新增每週洞察端點
fix(bot): 優雅處理缺失的用戶個人資料
docs(dev): 更新開發人員指南
test(qa): 為查詢處理器新增屬性測試
```

### 多租戶

資料隔離在**儲存庫層**強制執行。每個涉及用戶擁有資料 (閱讀清單、訂閱、對話) 的查詢都必須以 `user_id` 為範圍。絕不能獲取所有行並在 Python 中篩選。

```python
# ✅ 正確 — 在查詢層次範圍限定
async def get_reading_list(self, user_id: str) -> list[ReadingListItem]:
    return await self.db.table("reading_list").select("*").eq("user_id", user_id).execute()

# ❌ 錯誤 — 獲取所有行
async def get_reading_list(self) -> list[ReadingListItem]:
    all_items = await self.db.table("reading_list").select("*").execute()
    return [i for i in all_items if i["user_id"] == user_id]
```

### 服務 Mixin 模式

大型服務被拆分為 `backend/app/services/_mixins/` 下的 Mixin。每個 Mixin 處理一個領域 (文章、動態消息、閱讀清單、通知、用戶)。主要的 `SupabaseService` 透過多重繼承組合它們。

當添加新的服務方法時，請將它們放在適當的 Mixin 文件中，而不是主要服務類別。

### 錯誤處理

在 `backend/app/core/exceptions.py` 中定義特定領域的異常。在 API/機器人層捕獲特定異常並返回用戶友好的訊息。

```python
# 在 cog 或 API 處理器中
try:
    result = await service.do_something(user_id)
except RepositoryError as e:
    logger.error("用戶 %s 的資料庫錯誤: %s", user_id, e, exc_info=True)
    await interaction.followup.send("操作失敗，請重試。", ephemeral=True)
```

### 資料庫

- 無本地資料庫，無 Alembic 遷移 — 所有 Schema 變更都透過 Supabase SQL 編輯器完成。
- 遷移腳本位於 `backend/scripts/`。
- 使用 pgvector (`embedding VECTOR(1536)`) 對文章和對話進行語義搜尋。

### 前端資料獲取

所有伺服器狀態都使用 React Query。在 `frontend/lib/queryKeys.ts` 中集中定義查詢鍵，以避免快取衝突。

```typescript
// ✅ 使用 React Query
const { data, isLoading } = useQuery({
  queryKey: queryKeys.readingList(userId),
  queryFn: () => api.readingList.getAll(),
});
```

### i18n

所有面向用戶的字串必須同時存在於 `frontend/locales/en.json` 和 `frontend/locales/zh.json` 中。使用 `next-intl` 的 `useTranslations` Hook。pre-commit hook 將拒絕兩個語言環境文件鍵不匹配的提交。

---

## 參考資料

- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [discord.py Docs](https://discordpy.readthedocs.io/)
- [Supabase Docs](https://supabase.com/docs)
- [Groq API Docs](https://console.groq.com/docs)
- [Next.js 14 Docs](https://nextjs.org/docs)
- [shadcn/ui](https://ui.shadcn.com)
- [Hypothesis Docs](https://hypothesis.readthedocs.io/)
