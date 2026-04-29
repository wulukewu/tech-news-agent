# Requirements: Learning Path Active Integration

## Introduction

現有的學習路徑功能是被動的——用戶需要手動標記進度、手動查看推薦。本 spec 將學習路徑與現有的閱讀行為、proactive DM 系統串接，讓 agent 主動追蹤進度並在適當時機介入。

## Requirements

### Requirement 1: 閱讀行為自動同步進度

**User Story:** 當我在 dashboard 讀了一篇文章並評分，如果這篇文章跟我的學習目標相關，進度應該自動更新，不需要我手動標記。

#### Acceptance Criteria

1. WHEN 用戶對文章評分（rating >= 3），THE system SHALL 檢查該文章是否符合用戶任何進行中的學習路徑階段
2. WHEN 文章與學習階段相關（相關度 >= 0.6），THE system SHALL 自動呼叫 `ArticleRecommender.mark_article_completed()` 更新進度
3. WHEN 進度自動更新，THE system SHALL 不重複計算已手動標記的文章
4. 相關度判斷 SHALL 使用文章的 category 和 learning_stage 的 skills 做比對，不需要額外 LLM 呼叫

### Requirement 2: Proactive DM 優先推學習路徑文章

**User Story:** 我設定了學習目標後，每次收到的 DM 推薦應該優先包含符合我當前學習階段的文章。

#### Acceptance Criteria

1. WHEN `proactive_recommendation_job` 為用戶選文章時，THE system SHALL 先查詢該用戶是否有進行中的學習目標
2. WHEN 用戶有進行中的學習目標，THE system SHALL 從當前學習階段的推薦文章中優先選取，最多佔 DM 推薦總數的 60%
3. 推薦原因 SHALL 標明「符合你的 [目標名稱] 學習路徑 - [階段名稱] 階段」
4. WHEN 學習路徑文章不足，THE system SHALL 用一般偏好推薦補足剩餘名額

### Requirement 3: 學習停滯偵測與主動提醒

**User Story:** 如果我好幾天沒有學習進度，agent 應該主動提醒我，而不是讓學習目標默默擱置。

#### Acceptance Criteria

1. THE system SHALL 每天檢查所有進行中的學習目標，計算距上次進度更新的天數
2. WHEN 距上次進度更新超過 3 天，THE system SHALL 透過 Discord DM 發送提醒
3. 提醒訊息 SHALL 包含：目標名稱、當前進度百分比、下一篇推薦文章
4. WHEN 用戶已暫停（paused）學習目標，THE system SHALL 不發送提醒
5. 每個目標每週最多發送 2 次停滯提醒，避免騷擾
