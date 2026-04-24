# Tech News Agent Bugfix 技術設計文件

## Overview

本文件針對 Tech News Agent 中五個已確認的 Bug 進行技術設計。這些 Bug 涵蓋 Notion API 相容性錯誤、Docker 環境依賴問題、Scheduler 設定錯誤、功能缺失以及 Discord UI 持久化問題。修復策略以最小變更為原則，確保不影響現有正常運作的功能。

---

## Glossary

- **Bug_Condition (C)**：觸發 Bug 的條件 — 特定輸入或環境狀態導致系統行為不符預期
- **Property (P)**：修復後的預期正確行為
- **Preservation**：修復後必須維持不變的現有行為
- **isBugCondition(X)**：判斷輸入 X 是否觸發 Bug 的偽代碼函式
- **get_active_feeds()**：`notion_service.py` 中查詢 Notion Feeds 資料庫的方法
- **add_feed()**：`notion_service.py` 中待實作的新增 RSS 訂閱源方法
- **ReadLaterView**：`interactions.py` 中的 Discord UI View，包含「稍後閱讀」按鈕
- **persistent view**：Discord.py 中透過 `bot.add_view()` 在 Bot 重啟後仍可處理 interaction 的 View 機制
- **model_config**：Pydantic `BaseSettings` 的 meta 設定物件（`SettingsConfigDict`），非 `.env` 值的存取介面
- **Settings**：`app/core/config.py` 中的 Pydantic Settings 類別，負責讀取 `.env` 環境變數

---

## Bug Details

### Bug 1：Notion API `databases.query` AttributeError

#### Bug Condition

`notion-client>=2.2.1` 版本中，`AsyncClient` 的 `databases` 屬性不再提供 `query()` 方法，正確的呼叫方式為直接使用 `self.client.databases.query(database_id=...)`（若 SDK 仍支援）或改用 `self.client.request()` 底層呼叫。實際上，`notion-client` 2.x 的正確用法是 `await self.client.databases.query(database_id=...)` — 需確認實際 SDK 版本的正確 method 路徑。

**Formal Specification:**

```
FUNCTION isBugCondition_1(X)
  INPUT: X 為任何觸發 get_active_feeds() 或 add_to_read_later() 的呼叫
  OUTPUT: boolean

  RETURN notion_client_version >= "2.2.1"
         AND call_uses_deprecated_api_path(X)
         AND raises_AttributeError(X)
END FUNCTION
```

#### Examples

- `/news_now` 觸發 → `get_active_feeds()` → `self.client.databases.query(...)` → `AttributeError: 'DatabasesEndpoint' object has no attribute 'query'`
- 排程任務觸發 → 同上路徑 → 同樣錯誤，新聞無法發送
- 預期：呼叫正確 API 後回傳 `{"results": [...]}` 格式的 Notion 回應

---

### Bug 2：Docker 環境 `certifi` 缺少依賴 + SSL 修復平台限制

#### Bug Condition

`requirements.txt` 缺少 `certifi`，導致 Docker 環境 import 失敗。同時 `app/main.py` 無條件執行 macOS 專用的 SSL 修復，在 Linux 環境下造成不必要的副作用。

**Formal Specification:**

```
FUNCTION isBugCondition_2(X)
  INPUT: X 為應用程式啟動環境
  OUTPUT: boolean

  RETURN (is_docker_or_linux(X) AND certifi_not_in_requirements(X))
         OR (is_linux(X) AND ssl_patch_runs_unconditionally(X))
END FUNCTION
```

#### Examples

- Docker build → `pip install -r requirements.txt` → `certifi` 未安裝 → `import certifi` → `ModuleNotFoundError`
- Linux 環境啟動 → `os.environ["SSL_CERT_FILE"] = certifi.where()` 無條件執行 → 非必要的環境變數污染
- 預期：`certifi` 加入 `requirements.txt`；SSL patch 僅在 `sys.platform == "darwin"` 時執行

---

### Bug 3：Scheduler timezone 設定錯誤

#### Bug Condition

`settings.model_config` 是 Pydantic 的 `SettingsConfigDict` 物件（meta 設定），不是 `.env` 值的 dict。呼叫 `.get("timezone", "Asia/Taipei")` 永遠回傳預設值，無法讀取使用者設定的 `TIMEZONE` 環境變數。

**Formal Specification:**

```
FUNCTION isBugCondition_3(X)
  INPUT: X 為 AsyncIOScheduler 初始化呼叫
  OUTPUT: boolean

  RETURN uses_model_config_get_for_timezone(X)
         AND model_config_is_pydantic_meta_object(X)
         AND NOT reads_from_env_settings_field(X)
END FUNCTION
```

#### Examples

- `.env` 設定 `TIMEZONE=UTC` → `settings.model_config.get("timezone", "Asia/Taipei")` → 回傳 `"Asia/Taipei"`（忽略 .env）
- Scheduler 以錯誤 timezone 初始化 → 排程時間偏移
- 預期：`Settings` 類別新增 `timezone: str = "Asia/Taipei"` 欄位，Scheduler 使用 `settings.timezone`

---

### Bug 4：`/add_feed` 指令為空殼

#### Bug Condition

`NewsCommands.add_feed()` 只回傳佔位訊息，未呼叫任何 `NotionService` 方法。`NotionService` 也缺少 `add_feed()` 方法。

**Formal Specification:**

```
FUNCTION isBugCondition_4(X)
  INPUT: X 為 /add_feed 指令呼叫，包含 name, url, category 參數
  OUTPUT: boolean

  RETURN add_feed_command_has_no_notion_write(X)
         AND notion_service_missing_add_feed_method(X)
END FUNCTION
```

#### Examples

- 使用者執行 `/add_feed name:HackerNews url:https://... category:AI` → 回傳佔位訊息 → Notion 無新記錄
- 預期：Notion Feeds 資料庫新增一筆頁面，屬性包含 Name、URL、Category、Active（預設 True）

---

### Bug 5：`ReadLaterView` 重啟後按鈕失效

#### Bug Condition

`ReadLaterView` 雖設定 `timeout=None`，但未在 Bot 啟動時呼叫 `bot.add_view()` 重新註冊。Discord.py 的 persistent view 機制要求：(1) `timeout=None`，(2) 所有 Button 的 `custom_id` 固定且唯一，(3) Bot 啟動時呼叫 `bot.add_view(view_instance)`。

**Formal Specification:**

```
FUNCTION isBugCondition_5(X)
  INPUT: X 為 Bot 重啟後的 button interaction 事件
  OUTPUT: boolean

  RETURN bot_was_restarted(X)
         AND view_not_registered_via_add_view(X)
         AND interaction_targets_ReadLaterView_button(X)
END FUNCTION
```

#### Examples

- Bot 重啟 → 使用者點擊舊訊息的「稍後閱讀」按鈕 → Discord 回應 `This interaction failed`
- 目前 `ReadLaterButton` 的 `custom_id` 為 `read_later_{index}`（0-6），但 `article` 物件在重啟後不存在於 view 實例中
- 預期：Bot 啟動時註冊 persistent view；`custom_id` 攜帶足夠資訊（如 article URL hash）以在重啟後還原 article 資料

---

## Expected Behavior

### Preservation Requirements

**必須維持不變的行為：**

- `/news_now` 完整流程（抓取 → 評分 → 生成 → 發送）在 Notion 有啟用訂閱源時正常運作
- `NotionService.add_to_read_later()` 正確將文章寫入 Read Later 資料庫
- Bot 未重啟時，點擊「稍後閱讀」按鈕成功存入 Notion 並停用按鈕
- 排程任務每週五 17:00 自動觸發並發送新聞
- macOS 本地環境的 SSL 憑證修復邏輯繼續正常運作
- `get_active_feeds()` 回傳空清單時，系統回傳適當提示而非拋出例外

**Scope：**
所有不涉及上述五個 Bug 觸發條件的輸入，修復後行為應與修復前完全相同。

---

## Hypothesized Root Cause

### Bug 1

1. **API 版本不相容**：`notion-client` 2.x 改變了 `databases` endpoint 的 method 結構，`query()` 可能移至不同路徑或需要不同呼叫方式
2. **未查閱 SDK changelog**：原始碼直接使用 1.x 的 API 路徑，未隨版本升級更新

### Bug 2

1. **requirements.txt 遺漏**：`certifi` 在 macOS 開發環境可能已預裝，開發者未意識到需要明確列出
2. **平台假設**：SSL patch 程式碼寫在 module 頂層，未加平台判斷，假設所有環境都是 macOS

### Bug 3

1. **Pydantic v2 API 誤用**：`model_config` 在 Pydantic v2 是 `SettingsConfigDict` 類別屬性，不是 instance dict，`.get()` 方法行為與預期不同
2. **缺少 timezone 欄位**：`Settings` 類別未定義 `timezone` 欄位，導致開發者誤用 `model_config` 嘗試讀取

### Bug 4

1. **功能未完成**：原始碼有明確的 TODO 註解，`add_feed()` 方法從未被實作
2. **NotionService 缺少對應方法**：`notion_service.py` 只有 `get_active_feeds()` 和 `add_to_read_later()`，缺少 `add_feed()`

### Bug 5

1. **persistent view 機制未完整實作**：`timeout=None` 只是必要條件之一，還需要 `bot.add_view()` 和固定 `custom_id`
2. **article 物件無法在重啟後還原**：`ReadLaterButton` 持有 `article` 物件引用，重啟後記憶體中的 view 實例消失，article 資料遺失

---

## Correctness Properties

Property 1: Bug Condition — Notion API 正確呼叫

_For any_ 觸發 `get_active_feeds()` 的呼叫，在 `notion-client>=2.2.1` 環境下，修復後的函式 SHALL 使用正確的 API 路徑完成查詢，不拋出 `AttributeError`，並回傳 `List[RSSSource]`。

**Validates: Requirements 2.1, 2.2**

Property 2: Bug Condition — Docker 環境啟動成功

_For any_ 在 Docker/Linux 環境下的應用程式啟動，修復後 SHALL 成功安裝所有依賴（含 `certifi`），且 SSL patch 程式碼 SHALL 僅在 `sys.platform == "darwin"` 時執行。

**Validates: Requirements 2.3, 2.4**

Property 3: Bug Condition — Scheduler 正確讀取 timezone

_For any_ `AsyncIOScheduler` 初始化呼叫，修復後 SHALL 從 `settings.timezone` 讀取正確的 timezone 值，而非從 `model_config` meta 物件讀取。

**Validates: Requirements 2.5, 2.6**

Property 4: Bug Condition — `/add_feed` 寫入 Notion

_For any_ 包含有效 `name`、`url`、`category` 的 `/add_feed` 指令呼叫，修復後 SHALL 在 Notion Feeds 資料庫建立新頁面，並回傳成功訊息。

**Validates: Requirements 2.7, 2.8**

Property 5: Bug Condition — ReadLaterView 重啟後持久化

_For any_ Bot 重啟後的「稍後閱讀」按鈕 interaction，修復後 SHALL 正確處理回呼，不回應 `interaction failed`。

**Validates: Requirements 2.9, 2.10**

Property 6: Preservation — 現有功能不受影響

_For any_ 不觸發上述五個 Bug Condition 的輸入（正常 `/news_now` 流程、`add_to_read_later()`、Bot 未重啟時的按鈕點擊、排程觸發、macOS SSL 修復），修復後的程式碼 SHALL 產生與修復前完全相同的行為。

**Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5, 3.6**

---

## Fix Implementation

### Bug 1：修正 Notion API 呼叫

**File:** `app/services/notion_service.py`

**Changes:**

1. 確認 `notion-client` 2.x 正確的 `databases.query` 呼叫方式（根據 SDK 文件，`await self.client.databases.query(database_id=...)` 在 2.x 仍為正確路徑，問題可能在於 `data_sources.query(data_source_id=...)` 的混淆）
2. 將 `get_active_feeds()` 中的 API 呼叫改為正確路徑
3. 新增 `add_feed(name, url, category)` 方法（同時解決 Bug 4）

```python
# 修正前
results = await self.client.databases.query(
    database_id=self.feeds_db_id, ...
)

# 修正後（依實際 SDK 2.x 正確路徑）
results = await self.client.databases.query(
    database_id=self.feeds_db_id, ...
)
# 若 2.x 已移除此路徑，改用：
results = await self.client.request(
    path=f"databases/{self.feeds_db_id}/query",
    method="POST",
    body={...}
)
```

---

### Bug 2：修正 certifi 依賴與 SSL 平台判斷

**File 1:** `requirements.txt`

- 新增 `certifi>=2024.2.2`

**File 2:** `app/main.py`

- 將 SSL patch 包裹在平台判斷中

```python
# 修正前（無條件執行）
import certifi, ssl
os.environ["SSL_CERT_FILE"] = certifi.where()
os.environ["SSL_CERT_DIR"] = os.path.dirname(certifi.where())

# 修正後
import sys
if sys.platform == "darwin":
    import certifi
    os.environ["SSL_CERT_FILE"] = certifi.where()
    os.environ["SSL_CERT_DIR"] = os.path.dirname(certifi.where())
```

---

### Bug 3：修正 Scheduler timezone 讀取

**File 1:** `app/core/config.py`

- 在 `Settings` 類別新增 `timezone` 欄位

```python
class Settings(BaseSettings):
    # ... 現有欄位 ...
    timezone: str = "Asia/Taipei"  # 新增
```

**File 2:** `app/tasks/scheduler.py`

- 將 `settings.model_config.get("timezone", "Asia/Taipei")` 改為 `settings.timezone`

```python
# 修正前
scheduler = AsyncIOScheduler(timezone=settings.model_config.get("timezone", "Asia/Taipei"))

# 修正後
scheduler = AsyncIOScheduler(timezone=settings.timezone)
```

---

### Bug 4：實作 `NotionService.add_feed()`

**File 1:** `app/services/notion_service.py`

- 新增 `add_feed(name, url, category)` 方法

```python
async def add_feed(self, name: str, url: str, category: str) -> None:
    """新增一個 RSS 訂閱源至 Notion Feeds 資料庫。"""
    await self.client.pages.create(
        parent={"database_id": self.feeds_db_id},
        properties={
            "Name": {"title": [{"text": {"content": name}}]},
            "URL": {"url": url},
            "Category": {"select": {"name": category}},
            "Active": {"checkbox": True},
        }
    )
```

**File 2:** `app/bot/cogs/news_commands.py`

- 將 `add_feed` 指令改為實際呼叫 `NotionService.add_feed()`

```python
async def add_feed(self, interaction, name, url, category):
    await interaction.response.defer(thinking=True)
    try:
        notion = NotionService()
        await notion.add_feed(name, url, category)
        await interaction.followup.send(f"✅ 已成功新增 `{name}` ({category}) 至 Notion！\n🔗 {url}")
    except Exception as e:
        await interaction.followup.send(f"❌ 新增失敗：{e}")
```

---

### Bug 5：實作 ReadLaterView Persistent View

**核心問題分析：**
Discord persistent view 在 Bot 重啟後，只能透過 `custom_id` 識別按鈕，無法還原 `article` 物件。解決方案：將 article URL 編碼進 `custom_id`，在 callback 中從 `custom_id` 取得 URL，再從 Notion 或直接使用 URL 建立最小化的 article 資料。

**File 1:** `app/bot/cogs/interactions.py`

- `ReadLaterButton` 的 `custom_id` 改為 `read_later_{url_hash}`（使用 URL 的 MD5/SHA256 前綴）
- 在 `callback` 中從 `custom_id` 還原所需資料，或直接儲存 URL 至 Notion
- `ReadLaterView` 改為接受 `articles` 或空初始化（用於 `bot.add_view()`）

```python
import hashlib

class ReadLaterButton(discord.ui.Button):
    def __init__(self, article: ArticleSchema, index: int):
        url_hash = hashlib.md5(article.url.encode()).hexdigest()[:8]
        custom_id = f"read_later_{url_hash}"
        label_text = f"⭐ {article.title[:20]}..." if len(article.title) > 20 else f"⭐ {article.title}"
        super().__init__(style=discord.ButtonStyle.primary, label=label_text, custom_id=custom_id)
        self.article = article
```

**File 2:** `app/bot/client.py`

- 在 `setup_hook()` 中呼叫 `bot.add_view()` 註冊 persistent view

```python
async def setup_hook(self):
    await self.load_extension("app.bot.cogs.news_commands")
    await self.load_extension("app.bot.cogs.interactions")
    # 註冊 persistent view（空 articles 列表，僅用於重啟後的 interaction 路由）
    from app.bot.cogs.interactions import ReadLaterView
    self.add_view(ReadLaterView(articles=[]))
```

---

## Testing Strategy

### Validation Approach

測試策略分兩階段：先在未修復的程式碼上執行探索性測試，確認 Bug 確實存在並理解根本原因；再執行修復驗證測試，確認修復正確且不影響現有行為。

---

### Exploratory Bug Condition Checking

**Goal:** 在未修復程式碼上產生反例，確認根本原因分析。

**Test Plan:** 使用 mock 模擬 Notion client、Discord interaction、環境變數，在未修復程式碼上執行，觀察失敗模式。

**Test Cases:**

1. **Bug 1 探索**：mock `notion-client` 2.x 的 `databases` endpoint，呼叫 `get_active_feeds()`，預期拋出 `AttributeError`（未修復時失敗）
2. **Bug 2 探索**：在 Linux 環境模擬啟動，驗證 SSL patch 無條件執行（未修復時執行）
3. **Bug 3 探索**：設定 `TIMEZONE=UTC`，驗證 `scheduler.timezone` 仍為 `Asia/Taipei`（未修復時失敗）
4. **Bug 4 探索**：呼叫 `/add_feed` 指令，驗證 Notion `pages.create` 未被呼叫（未修復時確認）
5. **Bug 5 探索**：模擬 Bot 重啟後的 button interaction，驗證 `interaction failed`（未修復時確認）

**Expected Counterexamples:**

- Bug 1：`AttributeError: 'DatabasesEndpoint' object has no attribute 'query'`
- Bug 3：`scheduler.timezone == 'Asia/Taipei'` 即使 `.env` 設定 `TIMEZONE=UTC`
- Bug 4：`notion.pages.create` call count == 0

---

### Fix Checking

**Goal:** 驗證所有觸發 Bug Condition 的輸入，修復後產生預期行為。

**Pseudocode:**

```
FOR ALL X WHERE isBugCondition_N(X) DO
  result := fixedFunction(X)
  ASSERT expectedBehavior(result)
END FOR
```

**Test Cases:**

1. mock `notion-client` 2.x，呼叫修復後的 `get_active_feeds()`，ASSERT 回傳 `List[RSSSource]` 且無例外
2. 模擬 Linux 環境，ASSERT SSL patch 程式碼未執行
3. 設定 `TIMEZONE=UTC`，ASSERT `scheduler.timezone == "UTC"`
4. 呼叫修復後的 `/add_feed`，ASSERT `notion.pages.create` 被呼叫一次且參數正確
5. 模擬 Bot 重啟後的 button interaction，ASSERT callback 正確執行

---

### Preservation Checking

**Goal:** 驗證不觸發 Bug Condition 的輸入，修復前後行為完全相同。

**Pseudocode:**

```
FOR ALL X WHERE NOT isBugCondition_N(X) DO
  ASSERT originalFunction(X) = fixedFunction(X)
END FOR
```

**Testing Approach:** 使用 property-based testing 生成大量隨機輸入，驗證修復前後行為一致。

**Test Cases:**

1. **Preservation Test 1**：`add_to_read_later()` 在修復前後行為相同（mock Notion client，驗證 `pages.create` 參數不變）
2. **Preservation Test 2**：macOS 環境下 SSL patch 仍正常執行（`sys.platform == "darwin"` 分支）
3. **Preservation Test 3**：`/news_now` 完整流程在修復後仍正常運作（end-to-end mock test）
4. **Preservation Test 4**：Bot 未重啟時，「稍後閱讀」按鈕點擊行為不變

---

### Unit Tests

- 測試 `NotionService.get_active_feeds()` 使用正確 API 路徑（mock client）
- 測試 `NotionService.add_feed()` 呼叫 `pages.create` 並帶有正確屬性
- 測試 `Settings.timezone` 正確從 `.env` 讀取
- 測試 `main.py` SSL patch 在 `darwin` 執行、在 `linux` 跳過
- 測試 `ReadLaterButton.custom_id` 格式固定（不含 index，含 url hash）
- 測試 `add_feed` 指令在 Notion 寫入成功後回傳成功訊息

### Property-Based Tests

- 生成隨機 `ArticleSchema` 列表，驗證 `ReadLaterView` 的每個按鈕 `custom_id` 唯一且格式正確
- 生成隨機 `name/url/category` 組合，驗證 `add_feed()` 呼叫 `pages.create` 的參數結構始終正確
- 生成隨機 timezone 字串，驗證 `Settings.timezone` 正確傳遞至 `AsyncIOScheduler`

### Integration Tests

- 完整模擬 `/news_now` 流程（mock Notion + RSS + LLM），驗證修復後端到端正常
- 模擬 Docker 環境啟動，驗證所有依賴安裝成功且 SSL patch 跳過
- 模擬 Bot 重啟 → 點擊舊按鈕 → 驗證 Notion 寫入成功
