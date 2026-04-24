# read-later-button-missing 任務清單

## 任務

- [x] 1. 探索性測試：在未修復的程式碼上確認 Bug
  - [x] 1.1 在 `tests/test_bug_conditions.py` 中新增測試，模擬 `combined_view` 的組合邏輯，斷言 `combined_view.children` 中應包含 `ReadLaterButton`，預期在未修復時失敗
  - [x] 1.2 執行探索性測試，觀察失敗訊息，確認根本原因為 `ReadLaterView` 子元件從未被加入

- [x] 2. 實作修復
  - [x] 2.1 在 `app/bot/cogs/news_commands.py` 的 `news_now` 方法中，於組合 `combined_view` 的區塊加入 `ReadLaterView` 實例化與子元件迭代邏輯，限制最多加入 19 個 `ReadLaterButton`（確保總元件數 ≤ 25）

- [x] 3. 修復驗證測試（Fix Checking）
  - [x] 3.1 在 `tests/test_bug_conditions.py` 中新增測試，驗證修復後文章數 ≥ 1 時 `combined_view` 包含至少一個 `ReadLaterButton`
  - [x] 3.2 新增測試，驗證文章數為 1、5、19、20 時總元件數均 ≤ 25
  - [x] 3.3 新增測試，驗證文章數 = 0 時程式不崩潰且 `combined_view` 正常建立

- [x] 4. 保留測試（Preservation Checking）
  - [x] 4.1 在 `tests/test_preservation.py` 中新增屬性測試，隨機生成 1–50 篇文章，驗證 `FilterSelect` 始終存在於 `combined_view.children` 且為第一個元件（對應 Property 2）
  - [x] 4.2 新增屬性測試，隨機生成文章列表，驗證 `DeepDiveButton` 數量始終為 min(5, 文章數)（對應 Property 2）
  - [x] 4.3 新增屬性測試，驗證對任意文章列表，`ReadLaterButton` 數量 = min(len(articles), 19)（對應 Property 1）
