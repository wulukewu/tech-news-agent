# read-later-button-missing Bugfix 設計文件

## 概覽

在 `news_now` 指令中，`combined_view` 的組合邏輯只合併了 `FilterView` 與 `DeepDiveView` 的子元件，卻遺漏了 `ReadLaterView` 的 `ReadLaterButton`。修復方式為在組合 `combined_view` 時，額外將 `ReadLaterView` 的子元件加入，並確保總元件數不超過 Discord 的 25 個上限。

## 詞彙表

- **Bug_Condition (C)**：觸發 Bug 的條件——`combined_view` 組合時未加入 `ReadLaterView` 的子元件
- **Property (P)**：Bug 條件成立時的預期正確行為——週報訊息應同時顯示「稍後閱讀」按鈕
- **Preservation（保留）**：修復後不得改變的現有行為——`FilterSelect` 與 `DeepDiveButton` 的功能必須維持不變
- **`news_now`**：`app/bot/cogs/news_commands.py` 中的 slash command，負責抓取文章、生成週報並發送至 Discord
- **`combined_view`**：`news_now` 中組合多個 View 子元件的 `FilterView` 實例
- **`ReadLaterView`**：`app/bot/cogs/interactions.py` 中的 View，包含多個 `ReadLaterButton`
- **`DeepDiveView`**：`app/bot/cogs/interactions.py` 中的 View，包含最多 5 個 `DeepDiveButton`
- **Discord 元件上限**：Discord 每則訊息的 View 最多允許 25 個互動元件

## Bug 詳情

### Bug 條件

Bug 發生於 `news_now` 組合 `combined_view` 時，`ReadLaterView` 的子元件從未被加入。目前程式碼只迭代 `DeepDiveView` 的 `children`，完全沒有對 `ReadLaterView` 做相同操作。

**正式規格：**

```
FUNCTION isBugCondition(combined_view, read_later_view)
  INPUT: combined_view 為已組合的 FilterView 實例
         read_later_view 為 ReadLaterView 實例
  OUTPUT: boolean

  read_later_buttons = [c for c in read_later_view.children
                        if isinstance(c, ReadLaterButton)]

  RETURN len(read_later_buttons) > 0
         AND NOT ANY(isinstance(c, ReadLaterButton)
                     for c in combined_view.children)
END FUNCTION
```

### 範例

- 文章數 = 3：`combined_view` 應有 1（FilterSelect）+ 5（DeepDiveButton）+ 3（ReadLaterButton）= 9 個元件，實際只有 6 個，缺少 3 個 ReadLaterButton
- 文章數 = 10：應有 1 + 5 + 10 = 16 個元件，實際只有 6 個，缺少 10 個 ReadLaterButton
- 文章數 = 20：應有 1 + 5 + 19 = 25 個元件（上限截斷），實際只有 6 個，缺少 19 個 ReadLaterButton
- 文章數 = 0：`combined_view` 有 1 個元件，無 ReadLaterButton 可加入，行為正確（邊界情況）

## 預期行為

### 保留需求

**不得改變的行為：**

- `FilterSelect` 下拉選單必須繼續正常顯示與運作
- 最多 5 個 `DeepDiveButton` 必須繼續正常顯示與運作
- 點擊 `DeepDiveButton` 後 LLM 深度摘要的呼叫邏輯不得受影響
- 使用 `FilterSelect` 篩選文章的邏輯不得受影響

**範圍：**
所有不涉及 `ReadLaterButton` 加入邏輯的輸入，修復後行為應與修復前完全相同，包含：

- 滑鼠點擊 `DeepDiveButton`
- 使用 `FilterSelect` 下拉選單
- 週報文字內容的生成與截斷邏輯

## 假設根本原因

根據 Bug 描述，最可能的原因為：

1. **遺漏迭代 ReadLaterView.children**：`news_now` 中組合 `combined_view` 的程式碼只對 `DeepDiveView` 做了 `for item in DeepDiveView(...).children: combined_view.add_item(item)`，但沒有對 `ReadLaterView` 做相同操作

2. **元件數量未受控制**：加入 `ReadLaterButton` 後若文章數超過 19 篇，總元件數可能超過 Discord 的 25 個上限，需要截斷

3. **ReadLaterView 從未被實例化**：`ReadLaterView` 雖已在 `interactions.py` 中定義，但在 `news_now` 的組合邏輯中從未被建立實例

## 正確性屬性

Property 1：Bug 條件——週報訊息包含「稍後閱讀」按鈕

_For any_ 文章列表（長度 ≥ 1）執行 `news_now` 時，修復後的 `combined_view` SHALL 包含至少一個 `ReadLaterButton`，且總元件數不超過 25 個。

**Validates: Requirements 2.1, 2.2, 2.3**

Property 2：保留——現有元件行為不受影響

_For any_ 不涉及 `ReadLaterButton` 的互動（`FilterSelect` 操作、`DeepDiveButton` 點擊），修復後的程式碼 SHALL 產生與修復前完全相同的行為，保留所有現有的篩選與深度摘要功能。

**Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5**

## 修復實作

### 所需變更

假設根本原因分析正確：

**檔案**：`app/bot/cogs/news_commands.py`

**函式**：`news_now`

**具體變更**：

1. **實例化 ReadLaterView**：在組合 `combined_view` 的區塊中，建立 `ReadLaterView(articles=hardcore_articles)` 實例

2. **計算可加入的 ReadLaterButton 數量**：Discord 上限為 25 個元件，目前已有 FilterSelect(1) + DeepDiveButton(5) = 6 個，最多可再加入 19 個 ReadLaterButton

3. **迭代並加入子元件**：對 `ReadLaterView` 的 `children` 做截斷迭代，最多取前 19 個加入 `combined_view`

**修復前（有缺陷）：**

```python
combined_view = FilterView(articles=hardcore_articles)
for item in DeepDiveView(articles=hardcore_articles[:5]).children:
    combined_view.add_item(item)
await interaction.followup.send(content=draft, view=combined_view)
```

**修復後（正確）：**

```python
combined_view = FilterView(articles=hardcore_articles)
for item in DeepDiveView(articles=hardcore_articles[:5]).children:
    combined_view.add_item(item)
# 加入 ReadLaterButton，確保總元件數 ≤ 25
# 目前已有 FilterSelect(1) + DeepDiveButton(最多5) = 6，最多可再加 19 個
MAX_READ_LATER = 19
read_later_view = ReadLaterView(articles=hardcore_articles[:MAX_READ_LATER])
for item in read_later_view.children:
    combined_view.add_item(item)
await interaction.followup.send(content=draft, view=combined_view)
```

## 測試策略

### 驗證方式

測試策略分兩階段：先在未修復的程式碼上產生反例以確認 Bug，再驗證修復後的正確性與保留行為。

### 探索性 Bug 條件檢查

**目標**：在實作修復前，先產生反例以確認 Bug 的根本原因。若反例與預期不符，需重新分析。

**測試計畫**：模擬 `news_now` 的 `combined_view` 組合邏輯，斷言 `combined_view.children` 中應包含 `ReadLaterButton`，在未修復的程式碼上觀察失敗。

**測試案例**：

1. **基本案例**：文章數 = 3，斷言 `combined_view` 包含 `ReadLaterButton`（未修復時失敗）
2. **上限邊界**：文章數 = 20，斷言總元件數 ≤ 25（未修復時因缺少按鈕而失敗）
3. **空文章**：文章數 = 0，斷言 `combined_view` 不崩潰（邊界情況）

**預期反例**：

- `combined_view.children` 中不含任何 `ReadLaterButton` 實例
- 可能原因：`ReadLaterView` 從未被實例化，其子元件從未被加入

### 修復檢查

**目標**：驗證 Bug 條件成立時，修復後的函式產生預期行為。

**偽代碼：**

```
FOR ALL articles WHERE len(articles) >= 1 DO
  combined_view := build_combined_view_fixed(articles)
  ASSERT any(isinstance(c, ReadLaterButton) for c in combined_view.children)
  ASSERT len(combined_view.children) <= 25
END FOR
```

### 保留檢查

**目標**：驗證 Bug 條件不成立的輸入（非 ReadLaterButton 相關互動），修復後行為與修復前相同。

**偽代碼：**

```
FOR ALL interactions WHERE NOT involves_read_later_button(interaction) DO
  ASSERT original_behavior(interaction) = fixed_behavior(interaction)
END FOR
```

**測試方式**：屬性測試（Property-Based Testing）適合保留檢查，因為它能自動生成大量測試案例，覆蓋邊界情況。

**測試案例**：

1. **FilterSelect 保留**：驗證 `FilterSelect` 仍在 `combined_view.children` 中且為第一個元件
2. **DeepDiveButton 保留**：驗證 `DeepDiveButton` 數量仍為 min(5, 文章數)
3. **元件順序保留**：驗證 `FilterSelect` 在前、`DeepDiveButton` 居中、`ReadLaterButton` 在後

### 單元測試

- 測試文章數 1、5、19、20 時 `combined_view` 的元件組成
- 測試文章數 = 0 時不崩潰
- 測試總元件數在各文章數下均 ≤ 25

### 屬性測試（Property-Based Tests）

- 隨機生成 1–50 篇文章，驗證 `combined_view` 始終包含 `ReadLaterButton` 且總數 ≤ 25
- 隨機生成文章列表，驗證 `FilterSelect` 與 `DeepDiveButton` 的數量與行為不受影響
- 驗證對任意文章列表，`ReadLaterButton` 數量 = min(len(articles), 19)

### 整合測試

- 模擬完整 `news_now` 流程，驗證發送的 `combined_view` 包含三種元件
- 驗證點擊 `ReadLaterButton` 後能正確呼叫 Notion API
- 驗證修復後 `DeepDiveButton` 與 `FilterSelect` 的回呼行為不受影響
