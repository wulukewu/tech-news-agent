# Requirements Document: Proactive Recommendation Loop

## Introduction

現有的 proactive-learning-agent 已完成行為分析、偏好模型、權重調整等基礎設施，但缺少「主動送出通知」的閉環。用戶目前感受不到 agent 的存在，因為所有互動都是被動的（用戶問 → 系統答）。

本 spec 的目標是補上這個最後一哩路：**每次 fetch 完新文章後，agent 主動分析用戶偏好，挑選最相關的文章，透過 Discord DM 主動通知用戶，並允許用戶在 DM 裡直接回饋偏好。**

## Glossary

- **Proactive_DM**: agent 主動發出的 Discord DM，包含個人化推薦和原因說明
- **Recommendation_Reason**: 說明為什麼推薦這篇文章的理由（基於用戶評分歷史）
- **Inline_Feedback**: 用戶在 DM 裡直接點按鈕回饋「喜歡/不喜歡這類文章」
- **Preference_Update**: 根據 Inline_Feedback 即時更新 PreferenceModel 的動作

## Requirements

### Requirement 1: 文章 fetch 後自動觸發個人化推薦

**User Story:** 作為用戶，我希望每次系統抓完新文章後，能主動收到一則 DM，告訴我今天有哪幾篇最值得看，而不是自己去翻。

#### Acceptance Criteria

1. WHEN 背景 scheduler 完成一次 RSS fetch 並處理完文章，THE system SHALL 自動觸發個人化推薦流程
2. THE system SHALL 使用現有 PreferenceModel 的權重對新文章評分，挑選 top 3-5 篇
3. WHEN 用戶沒有足夠的評分歷史（少於 5 篇評分），THE system SHALL 改用 tinkering_index 排序，並在 DM 中說明「還在學習你的偏好」
4. THE system SHALL 只對開啟 DM 通知的用戶發送（沿用現有 `dm_notifications` 設定）
5. WHEN 當次 fetch 沒有新文章，THE system SHALL 不發送 DM

### Requirement 2: DM 內容包含推薦原因

**User Story:** 作為用戶，我希望 DM 裡不只是文章列表，還要告訴我為什麼推薦這篇，這樣我才知道 agent 真的了解我。

#### Acceptance Criteria

1. 每篇推薦文章 SHALL 附上一句推薦原因，例如「你之前給 Kubernetes 相關文章 4-5 星，這篇主題相似」
2. 推薦原因 SHALL 基於用戶實際的評分歷史，不可使用泛用說法
3. WHEN 用戶沒有評分歷史，推薦原因 SHALL 改為「這篇技術深度較高，符合本平台的精選標準」
4. DM 格式 SHALL 包含：文章標題、推薦原因、文章連結、Inline_Feedback 按鈕

### Requirement 3: Inline Feedback 按鈕

**User Story:** 作為用戶，我希望能在 DM 裡直接告訴 agent「這類文章不要再推了」或「多推這類」，不需要去開網頁設定。

#### Acceptance Criteria

1. 每篇推薦文章下方 SHALL 有兩個按鈕：「👍 多推這類」和「👎 少推這類」
2. WHEN 用戶點擊按鈕，THE system SHALL 即時呼叫 PreferenceModel 更新對應分類的權重
3. WHEN 用戶點擊「👍」，THE system SHALL 回覆「已記錄，會增加 [分類] 的推薦頻率」
4. WHEN 用戶點擊「👎」，THE system SHALL 回覆「已記錄，會減少 [分類] 的推薦頻率」
5. 按鈕點擊後 SHALL 變為 disabled，防止重複觸發

### Requirement 4: 推薦頻率控制

**User Story:** 作為用戶，我不希望每次 fetch 都收到 DM，這樣會很煩。

#### Acceptance Criteria

1. THE system SHALL 預設每天最多發送 1 次 Proactive_DM（即使 scheduler 一天跑多次）
2. THE system SHALL 記錄每個用戶最後一次收到 Proactive_DM 的時間
3. WHEN 距離上次 Proactive_DM 不足 20 小時，THE system SHALL 跳過該用戶
4. 用戶 SHALL 可在設定頁面調整頻率（每天 / 每兩天 / 每週）
