# 實作計畫：Discord 多租戶互動體驗

## 概述

本實作計畫將 Tech News Agent 的 Discord Bot 從單一使用者模式升級為多租戶架構。此重構將讓每個 Discord 使用者擁有獨立的訂閱、閱讀清單和個人化推薦，實現真正的多租戶 SaaS 服務。

核心改變：

- 自動使用者註冊：所有指令執行前自動呼叫 `get_or_create_user`
- 個人化訂閱：每個使用者可以訂閱不同的 RSS 來源
- 快速回應：`/news_now` 從資料庫讀取，不再即時抓取 RSS
- 完整整合：互動按鈕正確傳遞 `article_id` 並寫入資料庫
- 資料持久化：所有使用者操作都儲存在 Supabase

## 任務清單

- [x] 1. 建立使用者註冊中間件
  - [x] 1.1 建立 decorators.py 模組
    - 在 `app/bot/utils/` 目錄建立 `decorators.py` 檔案
    - 實作 `ensure_user_registered(interaction)` 函數
    - 呼叫 `supabase_service.get_or_create_user(interaction.user.id)`
    - 返回 user UUID
    - 處理註冊失敗的錯誤
    - _需求：1.1, 1.2, 1.3, 1.4, 1.5_

  - [x] 1.2 實作 require_user_registration 裝飾器
    - 建立 `@require_user_registration` 裝飾器
    - 在指令執行前自動呼叫 `ensure_user_registered`
    - 將 user_uuid 傳遞給被裝飾的函數
    - 處理例外並顯示使用者友善的錯誤訊息
    - _需求：1.1, 1.2, 1.3_

  - [x] 1.3 撰寫使用者註冊的單元測試
    - 測試新使用者註冊
    - 測試現有使用者返回相同 UUID
    - 測試並發註冊請求
    - 測試註冊失敗處理
    - _需求：1.1, 1.2, 1.5_

- [x] 2. 實作訂閱管理指令
  - [x] 2.1 建立 subscription_commands.py 模組
    - 在 `app/bot/cogs/` 目錄建立 `subscription_commands.py` 檔案
    - 建立 `SubscriptionCommands` Cog 類別
    - 註冊到 bot
    - _需求：2.1, 2.2_

  - [x] 2.2 實作 /add_feed 指令
    - 接受 name, url, category 參數
    - 呼叫 `ensure_user_registered` 取得 user UUID
    - 檢查 feeds 表是否已存在該 URL
    - 若不存在則插入新 feed 記錄
    - 呼叫 `supabase_service.subscribe_to_feed(discord_id, feed_id)`
    - 處理重複訂閱（顯示友善訊息）
    - 驗證 URL 格式
    - 發送確認訊息
    - _需求：2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7, 2.8_

  - [x] 2.3 實作 /list_feeds 指令
    - 呼叫 `ensure_user_registered` 取得 user UUID
    - 呼叫 `supabase_service.get_user_subscriptions(discord_id)`
    - 顯示訂閱源列表（name, url, category）
    - 按 subscribed_at 降序排序
    - 使用 ephemeral 回應
    - 處理空訂閱清單
    - _需求：10.1, 10.2, 10.3, 10.4, 10.5, 10.6, 10.7_

  - [x] 2.4 實作 /unsubscribe_feed 指令
    - 接受 feed_name 或 feed_id 參數
    - 呼叫 `ensure_user_registered` 取得 user UUID
    - 呼叫 `supabase_service.unsubscribe_from_feed(discord_id, feed_id)`
    - 處理不存在的訂閱（顯示友善訊息）
    - 發送確認訊息
    - _需求：11.1, 11.2, 11.3, 11.4, 11.5, 11.6_

  - [x] 2.5 撰寫訂閱管理的單元測試
    - 測試 /add_feed 新增新 feed
    - 測試 /add_feed 訂閱現有 feed
    - 測試 /add_feed 重複訂閱
    - 測試 /list_feeds 顯示訂閱清單
    - 測試 /list_feeds 空清單
    - 測試 /unsubscribe_feed 取消訂閱
    - 測試 /unsubscribe_feed 不存在的訂閱
    - _需求：2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7, 2.8, 10.1, 10.2, 10.3, 10.4, 10.5, 10.6, 10.7, 11.1, 11.2, 11.3, 11.4, 11.5, 11.6_

- [x] 3. 重構 /news_now 指令
  - [x] 3.1 修改 news_commands.py 移除 RSS 抓取
    - 移除 `rss_service.fetch_all_feeds()` 呼叫
    - 移除 `llm_service.evaluate_batch()` 呼叫
    - 移除 `supabase_service.insert_articles()` 呼叫
    - 保留 `defer(thinking=True)` 以顯示載入狀態
    - _需求：3.1, 3.2_

  - [x] 3.2 實作從資料庫查詢文章
    - 呼叫 `ensure_user_registered` 取得 user UUID
    - 呼叫 `supabase_service.get_user_subscriptions(discord_id)` 取得訂閱清單
    - 檢查使用者是否有訂閱（若無則提示訂閱）
    - 查詢 articles 表，篩選條件：
      - `feed_id IN (user's subscribed feed_ids)`
      - `published_at >= NOW() - INTERVAL '7 days'`
      - `tinkering_index IS NOT NULL`
    - 按 `tinkering_index DESC` 排序
    - 限制 20 筆結果
    - _需求：3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.8, 3.9_

  - [x] 3.3 建立文章顯示格式
    - 將查詢結果轉換為 ArticleSchema 物件
    - 按 category 分組顯示
    - 使用 tinkering_index 顯示火焰圖示（🔥）
    - 限制訊息長度在 2000 字元內
    - 處理空結果（提示等待背景排程器）
    - _需求：3.7_

  - [x] 3.4 更新互動元件傳遞 article_id
    - 修改 `FilterView` 接受包含 article_id 的文章列表
    - 修改 `DeepDiveButton` 接受 article_id
    - 修改 `ReadLaterButton` 接受 article_id 和 title
    - 確保所有按鈕的 custom_id 包含完整的 UUID
    - _需求：9.1, 9.2, 9.3, 9.4, 9.5, 9.6_

  - [x] 3.5 撰寫 /news_now 的單元測試
    - 測試無訂閱時的提示訊息
    - 測試有訂閱但無文章時的提示訊息
    - 測試正常查詢並顯示文章
    - 測試文章按 tinkering_index 排序
    - 測試文章限制為 20 筆
    - 測試時間窗口過濾（7 天）
    - 測試不觸發 RSS 抓取
    - 測試不觸發 LLM 分析
    - _需求：3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.8, 3.9_

- [x] 4. 更新互動按鈕整合
  - [x] 4.1 重構 ReadLaterButton
    - 修改 `__init__` 接受 `article_id: UUID` 和 `article_title: str`
    - 設定 custom*id 為 `f"read_later*{article_id}"`
    - 在 callback 中解析 custom_id 取得 article_id
    - 呼叫 `supabase_service.save_to_reading_list(discord_id, article_id)`
    - 設定初始 status 為 'Unread'
    - 成功後禁用按鈕
    - 發送 ephemeral 確認訊息
    - 處理錯誤並記錄日誌
    - _需求：4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 4.7, 4.8, 9.1, 9.2, 9.3, 9.4, 9.5, 9.6_

  - [x] 4.2 重構 MarkReadButton
    - 修改 `__init__` 接受 `article_id: UUID` 和 `article_title: str`
    - 設定 custom*id 為 `f"mark_read*{article_id}"`
    - 在 callback 中解析 custom_id 取得 article_id
    - 呼叫 `supabase_service.update_article_status(discord_id, article_id, 'Read')`
    - 自動更新 updated_at 時間戳
    - 成功後禁用按鈕
    - 發送 ephemeral 確認訊息
    - 處理文章不在閱讀清單的情況（自動加入並標記為已讀）
    - _需求：5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 5.7, 9.1, 9.2, 9.3, 9.4, 9.5, 9.6_

  - [x] 4.3 更新 RatingSelect
    - 確認 custom_id 包含 article_id
    - 在 callback 中解析 custom_id 取得 article_id
    - 呼叫 `supabase_service.update_article_rating(discord_id, article_id, rating)`
    - 驗證 rating 範圍（1-5）
    - 自動更新 updated_at 時間戳
    - 發送 ephemeral 確認訊息
    - 處理文章不在閱讀清單的情況（自動加入並設定評分）
    - _需求：7.1, 7.2, 7.3, 7.4, 7.5, 7.6, 9.1, 9.2, 9.3, 9.4, 9.5, 9.6_

  - [x] 4.4 更新 FilterSelect
    - 確保過濾後的文章包含 article_id
    - 更新顯示格式以支援新的資料結構
    - 保持 ephemeral 回應
    - _需求：3.7_

  - [x] 4.5 更新 DeepDiveButton
    - 修改 `__init__` 接受完整的 ArticleSchema 物件（包含 article_id）
    - 保持現有的 LLM 深度分析功能
    - 確保 custom_id 包含 article_id
    - _需求：9.1, 9.2, 9.3_

  - [x] 4.6 撰寫互動按鈕的單元測試
    - 測試 ReadLaterButton 儲存文章
    - 測試 ReadLaterButton 重複儲存
    - 測試 MarkReadButton 更新狀態
    - 測試 MarkReadButton 自動加入閱讀清單
    - 測試 RatingSelect 更新評分
    - 測試 RatingSelect 驗證評分範圍
    - 測試 custom_id 解析
    - 測試按鈕禁用
    - 測試錯誤處理
    - _需求：4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 4.7, 4.8, 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 5.7, 7.1, 7.2, 7.3, 7.4, 7.5, 7.6_

- [x] 5. 更新閱讀清單指令
  - [x] 5.1 驗證 /reading_list view 整合
    - 確認 `get_reading_list` 返回包含 article_id 的 ReadingListItem
    - 確認 MarkAsReadButton 使用 article_id
    - 確認 RatingSelect 使用 article_id
    - 確認分頁功能正常運作
    - 確認 ephemeral 回應
    - _需求：6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 6.7, 6.8, 6.9_

  - [x] 5.2 驗證 /reading_list recommend 整合
    - 確認查詢高評分文章（4-5 星）
    - 確認 LLM 生成個人化推薦
    - 確認 ephemeral 回應
    - 處理無高評分文章的情況
    - 處理 LLM 生成失敗
    - _需求：8.1, 8.2, 8.3, 8.4, 8.5, 8.6_

  - [x] 5.3 撰寫閱讀清單的整合測試
    - 測試完整流程：儲存 → 查看 → 評分 → 標記已讀
    - 測試分頁導航
    - 測試多使用者隔離
    - 測試推薦功能
    - _需求：6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 6.7, 6.8, 6.9, 8.1, 8.2, 8.3, 8.4, 8.5, 8.6_

- [x] 6. 實作持久化視圖
  - [x] 6.1 註冊持久化視圖
    - 在 bot 的 `setup_hook` 中註冊所有持久化視圖
    - 設定所有互動視圖的 `timeout=None`
    - 實作視圖重建邏輯（從 custom_id 重建狀態）
    - _需求：14.1, 14.2, 14.3, 14.4, 14.5_

  - [x] 6.2 處理 bot 重啟後的互動
    - 實作 custom_id 解析邏輯
    - 從資料庫重新載入必要資料
    - 處理原始訊息上下文遺失的情況
    - 記錄重啟後的互動日誌
    - _需求：14.3, 14.4, 14.5_

  - [x] 6.3 撰寫持久化視圖的測試
    - 測試 bot 重啟後按鈕仍可運作
    - 測試 custom_id 解析
    - 測試資料重新載入
    - 測試訊息上下文遺失處理
    - _需求：14.1, 14.2, 14.3, 14.4, 14.5_

- [x] 7. 實作錯誤處理與日誌
  - [x] 7.1 統一錯誤處理
    - 為所有指令新增 try-except 包裹
    - 記錄完整錯誤上下文和堆疊追蹤
    - 顯示使用者友善的錯誤訊息（繁體中文）
    - 不暴露內部錯誤細節
    - 使用 ephemeral 訊息顯示錯誤
    - _需求：12.1, 12.2, 12.3, 12.4, 12.5, 12.6_

  - [x] 7.2 實作全面的日誌記錄
    - 記錄所有指令執行（user_id, command_name）
    - 記錄所有按鈕互動（user_id, custom_id）
    - 記錄所有資料庫操作（operation_type, affected_records）
    - 記錄所有錯誤（ERROR 級別，包含堆疊追蹤）
    - 使用適當的日誌級別（INFO, WARNING, ERROR）
    - 不記錄敏感資訊（API keys, passwords）
    - _需求：17.1, 17.2, 17.3, 17.4, 17.5, 17.6_

  - [x] 7.3 實作並發操作處理
    - 使用資料庫約束處理並發訂閱
    - 使用 UPSERT 邏輯處理並發閱讀清單操作
    - 確保使用者註冊的冪等性
    - 不阻塞其他使用者的操作
    - _需求：13.1, 13.2, 13.3, 13.4, 13.5_

  - [x] 7.4 撰寫錯誤處理的測試
    - 測試資料庫連線失敗
    - 測試並發操作
    - 測試無效輸入驗證
    - 測試錯誤訊息格式
    - 測試日誌記錄
    - _需求：12.1, 12.2, 12.3, 12.4, 12.5, 12.6, 13.1, 13.2, 13.3, 13.4, 13.5, 17.1, 17.2, 17.3, 17.4, 17.5, 17.6_

- [x] 8. 實作資料驗證
  - [x] 8.1 實作輸入驗證函數
    - 驗證 feed URL 格式（HTTP/HTTPS）
    - 驗證 rating 範圍（1-5）
    - 驗證 status 值（'Unread', 'Read', 'Archived'）
    - 驗證 UUID 格式
    - 截斷長文字欄位（title: 2000, summary: 5000）
    - _需求：16.1, 16.2, 16.3, 16.4, 16.5, 16.6_

  - [x] 8.2 整合驗證到指令處理器
    - 在 /add_feed 中驗證 URL
    - 在 RatingSelect 中驗證 rating
    - 在所有地方驗證 UUID 格式
    - 在資料庫操作前截斷文字
    - _需求：16.1, 16.2, 16.3, 16.4, 16.5_

  - [x] 8.3 撰寫資料驗證的測試
    - 測試無效 URL 被拒絕
    - 測試無效 rating 被拒絕
    - 測試無效 status 被拒絕
    - 測試無效 UUID 被拒絕
    - 測試長文字被截斷
    - _需求：16.1, 16.2, 16.3, 16.4, 16.5_

- [x] 9. 效能優化
  - [x] 9.1 實作查詢優化
    - 使用資料庫索引（已存在於 Phase 1）
    - 限制查詢結果數量（20 筆文章）
    - 使用 SELECT 指定欄位而非 SELECT \*
    - 快取使用者訂閱清單（指令執行期間）
    - _需求：15.1, 15.2, 15.3, 15.4, 15.6_

  - [x] 9.2 實作回應時間優化
    - 確保 /news_now 在 3 秒內回應
    - 確保 /reading_list view 在 2 秒內回應
    - 對可能超過 3 秒的操作使用 defer()
    - 限制顯示的文章數量
    - _需求：15.1, 15.2, 15.5, 15.6_

  - [x] 9.3 實作記憶體管理
    - 不一次載入所有文章到記憶體
    - 使用分頁處理大結果集
    - 指令執行後清理資源
    - 避免在按鈕/選單實例中儲存大物件
    - _需求：15.4, 15.6_

  - [x] 9.4 撰寫效能測試
    - 測試 /news_now 回應時間
    - 測試 /reading_list view 回應時間
    - 測試大量文章的查詢效能
    - 測試並發使用者操作
    - _需求：15.1, 15.2, 15.3, 15.4, 15.5, 15.6_

- [x] 10. 整合測試與端到端驗證
  - [x] 10.1 撰寫完整使用者旅程測試
    - 測試：註冊 → 訂閱 → 查看文章 → 儲存到閱讀清單 → 評分 → 獲得推薦
    - 測試多使用者隔離（User A 的訂閱不影響 User B）
    - 測試並發操作（多個使用者同時訂閱）
    - 測試 bot 重啟後的持久化視圖
    - _需求：所有需求的整合驗證_

  - [x] 10.2 撰寫向後相容性測試
    - 測試與 Phase 3 資料庫結構的相容性
    - 測試處理背景排程器建立的文章
    - 測試處理尚未訂閱任何 feed 的使用者
    - 測試不需要資料庫遷移
    - _需求：18.1, 18.2, 18.3, 18.4, 18.5_

  - [x] 10.3 執行手動端到端測試
    - 在測試環境部署 bot
    - 手動執行所有指令
    - 測試所有互動按鈕
    - 驗證資料正確儲存到資料庫
    - 驗證多使用者隔離
    - 驗證錯誤處理
    - _需求：所有需求的手動驗證_

- [x] 11. 文件更新
  - [x] 11.1 更新 README.md
    - 記錄新的多租戶架構
    - 更新指令列表（新增 /add_feed, /list_feeds, /unsubscribe_feed）
    - 更新 /news_now 的行為說明（從資料庫讀取）
    - 新增訂閱管理指南
    - 新增故障排除提示
    - _需求：所有需求的文件化_

  - [x] 11.2 建立使用者指南
    - 如何訂閱 RSS 來源
    - 如何查看個人化新聞
    - 如何管理閱讀清單
    - 如何獲得個人化推薦
    - 常見問題解答
    - _需求：所有需求的使用者文件_

  - [x] 11.3 建立開發者文件
    - 多租戶架構說明
    - 資料流程圖
    - API 參考
    - 測試指南
    - 部署指南
    - _需求：所有需求的開發者文件_

- [x] 12. Final Checkpoint - 完整驗證
  - 執行所有單元測試
  - 執行所有整合測試
  - 執行效能測試
  - 執行手動端到端測試
  - 檢查測試覆蓋率 ≥ 90%
  - 驗證所有 18 個需求都被滿足
  - 檢查程式碼品質和文件完整性
  - 如有問題請詢問使用者

## 注意事項

### 實作順序

1. 先實作使用者註冊中間件（基礎設施）
2. 再實作訂閱管理指令（核心功能）
3. 然後重構 /news_now（主要變更）
4. 接著更新互動按鈕（整合）
5. 最後實作測試和文件

### 錯誤處理原則

- 所有指令都使用 try-except 包裹
- 所有錯誤都記錄完整上下文
- 使用者看到的錯誤訊息要友善且可操作
- 不暴露內部錯誤細節
- 使用 ephemeral 訊息顯示錯誤

### 效能考量

- /news_now 必須在 3 秒內回應
- /reading_list view 必須在 2 秒內回應
- 使用資料庫索引優化查詢
- 限制查詢結果數量
- 快取使用者訂閱清單

### 向後相容性

- Phase 4 不需要資料庫遷移
- 使用 Phase 1 建立的資料庫結構
- 處理背景排程器（Phase 3）建立的文章
- 處理尚未訂閱任何 feed 的使用者

### 測試要求

- 單元測試覆蓋所有新功能
- 整合測試驗證完整流程
- 效能測試確保回應時間
- 手動測試驗證使用者體驗
- 測試覆蓋率 ≥ 90%

## 參考資料

- **需求文件**：`.kiro/specs/discord-multi-tenant-ui/requirements.md`
- **設計文件**：`.kiro/specs/discord-multi-tenant-ui/design.md`
- **Phase 1 資料庫結構**：`scripts/init_supabase.sql`
- **Phase 2 資料存取層**：`app/services/supabase_service.py`
- **Phase 3 背景排程器**：`app/tasks/scheduler.py`
- **現有 Discord 指令**：`app/bot/cogs/news_commands.py`, `app/bot/cogs/reading_list.py`
- **現有互動元件**：`app/bot/cogs/interactions.py`
