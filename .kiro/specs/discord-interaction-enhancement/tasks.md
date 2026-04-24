# 任務清單：Discord 互動增強功能

## 任務

- [x] 1. 新增 LLMService.generate_deep_dive 方法
  - [x] 1.1 在 `app/services/llm_service.py` 中實作 `generate_deep_dive(self, article: ArticleSchema) -> str` 非同步方法
    - 使用已存在的 `SUMMARIZE_MODEL = "llama-3.3-70b-versatile"` 常數
    - 設定 `max_tokens=600`
    - 系統提示要求以繁體中文輸出，包含核心技術概念、應用場景、潛在風險、建議下一步
    - 提示輸入使用 `article.title`、`article.content_preview`、`article.source_category`，以及 `article.ai_analysis`（`AIAnalysis` 物件，含 `reason`、`actionable_takeaway`、`tinkering_index` 欄位）
    - 當 `content_preview` 為空字串時，僅以 `title` 作為輸入仍嘗試生成
    - API 呼叫失敗時拋出 `LLMServiceError`（已存在於 `app/core/exceptions.py`）；空回應時回傳預設字串 `"無法生成深度摘要內容。"`
    - _需求：5.1、5.2、5.3、5.4、5.5_

  - [x] 1.2 撰寫 `generate_deep_dive` 的單元測試
    - 測試使用 `SUMMARIZE_MODEL`（llama-3.3-70b-versatile）
    - 測試系統提示包含「繁體中文」
    - 測試 `max_tokens` 為 600
    - 測試 `content_preview` 為空時 prompt 仍包含 `title`
    - _需求：5.2、5.3、5.4、5.5_

  - [x] 1.3 撰寫屬性測試：generate_deep_dive prompt 包含文章關鍵欄位（屬性 6）
    - `# Feature: discord-interaction-enhancement, Property 6: generate_deep_dive 的 prompt 包含文章關鍵欄位`
    - 使用 Hypothesis 生成隨機 `ArticleSchema`（含 `content_preview` 為空的邊界情況），mock LLM 呼叫，驗證 prompt 包含 `title`，且 `content_preview` 非空時也包含 `content_preview`
    - _需求：5.2、5.4_

- [x] 2. 實作 FilterSelect 與 FilterView 元件
  - [x] 2.1 在 `app/bot/cogs/interactions.py` 中新增 `FilterSelect(discord.ui.Select)` 類別
    - `__init__` 接受 `articles: List[ArticleSchema]`
    - 使用 `Counter` 從 `source_category` 提取出現頻率最高的前 24 個分類
    - 選項清單第一個為 `discord.SelectOption(label="📋 顯示全部", value="__all__")`
    - `placeholder` 設為 `"請選擇分類篩選文章…"`
    - _需求：1.2、1.3、1.4、1.5_

  - [x] 2.2 實作 `FilterSelect.callback`
    - 選擇 `"__all__"` 時格式化所有文章的完整報表，以 `ephemeral=True` 回傳
    - 選擇特定分類時篩選 `source_category` 相符的文章；無對應文章時回傳 `"⚠️ 此分類目前沒有文章。"`
    - 報表內容超過 2000 字元時截斷至 1997 字元並附加 `"..."`
    - 發生例外時 `logger.error` 記錄，回傳 `"❌ 篩選時發生錯誤，請稍後再試。"` ephemeral
    - _需求：2.1、2.2、2.3、2.4、2.5_

  - [x] 2.3 新增 `FilterView(discord.ui.View)` 類別
    - `timeout=None`，在 `__init__` 中呼叫 `self.add_item(FilterSelect(articles))`
    - _需求：1.1、6.1_

  - [x] 2.4 撰寫 FilterSelect 與 FilterView 的單元測試
    - 測試 `FilterSelect` placeholder 文字為 `"請選擇分類篩選文章…"`
    - 測試選擇「顯示全部」時回傳所有文章的報表
    - 測試選擇不存在分類時回傳 `"⚠️ 此分類目前沒有文章。"`
    - 測試超過 24 個分類時選項數量不超過 25（24 分類 + 1 顯示全部）
    - _需求：1.2、1.3、1.4、1.5、2.1、2.2、2.4_

  - [x] 2.5 撰寫屬性測試：FilterSelect 選項建構（屬性 1）
    - `# Feature: discord-interaction-enhancement, Property 1: FilterSelect 選項包含所有分類且「顯示全部」排第一`
    - 使用 Hypothesis 生成隨機 `ArticleSchema` 列表，驗證第一個選項 value 為 `"__all__"`，其餘選項包含所有 `source_category`（最多 24 個）
    - _需求：1.2、1.3、1.4_

  - [x] 2.6 撰寫屬性測試：訊息截斷不變量（屬性 2）
    - `# Feature: discord-interaction-enhancement, Property 2: 訊息截斷不變量`
    - 使用 Hypothesis 生成隨機長字串，驗證截斷後長度恰好為 2000，末尾三個字元為 `"..."`
    - _需求：2.3、4.6_

  - [x] 2.7 撰寫屬性測試：篩選結果分類一致性（屬性 3）
    - `# Feature: discord-interaction-enhancement, Property 3: 篩選結果只包含指定分類的文章`
    - 使用 Hypothesis 生成隨機文章列表和分類值，驗證篩選後每篇文章的 `source_category` 都等於所選分類
    - _需求：2.1_

- [x] 3. 實作 DeepDiveButton 與 DeepDiveView 元件
  - [x] 3.1 在 `app/bot/cogs/interactions.py` 中新增 `DeepDiveButton(discord.ui.Button)` 類別
    - 標籤格式：`f"📖 {article.title[:20]}..."` 若標題超過 20 字元，否則 `f"📖 {article.title}"`
    - `custom_id` 格式：`f"deep_dive_{hashlib.md5(str(article.url).encode()).hexdigest()[:8]}"`（與現有 `ReadLaterButton` 格式一致）
    - `style=discord.ButtonStyle.secondary`
    - _需求：3.2、3.3_

  - [x] 3.2 實作 `DeepDiveButton.callback`
    - `await interaction.response.defer(ephemeral=True)`
    - 呼叫 `LLMService().generate_deep_dive(self.article)`
    - 結果超過 2000 字元時截斷至 1997 字元並附加 `"..."`
    - 以 `interaction.followup.send(ephemeral=True)` 回傳
    - 發生例外時 `logger.error` 記錄，回傳 `"❌ 生成深度摘要時發生錯誤，請稍後再試。"` ephemeral
    - _需求：4.1、4.2、4.5、4.6、4.7_

  - [x] 3.3 新增 `DeepDiveView(discord.ui.View)` 類別
    - `timeout=None`，在 `__init__` 中對 `articles[:5]` 各加入一個 `DeepDiveButton`
    - _需求：3.1、3.4、6.2_

  - [x] 3.4 撰寫 DeepDiveButton 與 DeepDiveView 的單元測試
    - 測試按鈕標籤截斷邏輯（超過 20 字元時附加 `...`）
    - 測試 `custom_id` 格式符合 `"deep_dive_{md5[:8]}"`
    - _需求：3.2、3.3_

  - [x] 3.5 撰寫屬性測試：DeepDiveView 按鈕數量（屬性 4）
    - `# Feature: discord-interaction-enhancement, Property 4: DeepDiveView 按鈕數量不超過上限`
    - 使用 Hypothesis 生成不同長度的文章列表，驗證 `len(view.children) == min(len(articles), 5)`
    - _需求：3.1、3.4_

  - [x] 3.6 撰寫屬性測試：DeepDiveButton 標籤與 custom_id 格式（屬性 5）
    - `# Feature: discord-interaction-enhancement, Property 5: DeepDiveButton 標籤與 custom_id 格式正確性`
    - 使用 Hypothesis 生成隨機 `ArticleSchema`，驗證標籤符合截斷規則，`custom_id` 符合 `"deep_dive_{md5[:8]}"` 格式
    - _需求：3.2、3.3_

  - [x] 3.7 撰寫屬性測試：View timeout 不變量（屬性 7）
    - `# Feature: discord-interaction-enhancement, Property 7: View 持久性 timeout 不變量`
    - 使用 Hypothesis 生成隨機文章列表，驗證 `FilterView` 和 `DeepDiveView` 實例的 `timeout` 屬性為 `None`
    - _需求：6.1、6.2_

- [x] 4. 修改 NewsCommands.news_now 整合新 View
  - [x] 4.1 在 `app/bot/cogs/news_commands.py` 中匯入 `FilterView`、`DeepDiveView`（與現有 `ReadLaterView` 匯入並列）
    - _需求：1.1、3.1_

  - [x] 4.2 建立組合 View：以 `FilterView(articles=hardcore_articles)` 為基底，將 `DeepDiveView(articles=hardcore_articles[:5]).children` 逐一加入
    - _需求：1.1、3.1_

  - [x] 4.3 將 `interaction.followup.send` 的 `view` 參數替換為組合 View
    - 保留現有 `ReadLaterView` 的匯入，但在此步驟中以組合 View 取代其在 `followup.send` 中的使用（`ReadLaterView` 類別本身不刪除，仍在 `interactions.py` 中存在）
    - _需求：1.1、3.1_

- [x] 5. 修改 TechNewsBot.setup_hook 註冊持久性 View
  - [x] 5.1 在 `app/bot/client.py` 的 `setup_hook` 中，在現有 `self.add_view(ReadLaterView(articles=[]))` 之後新增：

    ```python
    self.add_view(FilterView(articles=[]))
    self.add_view(DeepDiveView(articles=[]))
    ```

    - 匯入語句更新為 `from app.bot.cogs.interactions import ReadLaterView, FilterView, DeepDiveView`
    - _需求：6.3_

  - [x] 5.2 以 try/except 包裝三個 `add_view` 呼叫，捕捉例外時以 `logger.warning` 記錄，不拋出例外
    - _需求：6.4_

- [x] 6. 最終檢查點
  - 確認所有測試通過，如有疑問請向用戶確認。
