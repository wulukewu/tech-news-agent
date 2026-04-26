# Requirements: DM Conversation Memory & Preference Profile

## Overview

讓 bot 在 Discord DM 裡接收用戶的自然語言回覆，累積成對話記憶，
每天用 LLM 濃縮成偏好摘要，推薦時當作 context 使用。
用戶可在 Discord 和前端查看、編輯自己的偏好摘要。

## Requirements

### 1. DM 對話收集
- Bot 在 DM 裡偵測用戶的一般訊息（非指令）
- 存入 `dm_conversations` 表（user_id, content, created_at）
- 回覆簡短確認：「已記錄，這會幫助我更了解你的偏好 👍」
- 忽略 bot 自己發的訊息

### 2. 每日偏好摘要更新
- 每天 11:00 跑一次，對有新 DM 對話的用戶
- 用 Llama 3.1 8B 把最近 30 則對話濃縮成 200 字以內的偏好摘要
- 存入 `preference_model.preference_summary` 欄位（新增）

### 3. 推薦時使用摘要
- `_build_recommendations` 把 preference_summary 加進推薦原因生成邏輯
- 有摘要時推薦原因更精準（語意匹配而非只看分類）

### 4. Discord 指令 `/my_profile`
- 顯示目前的偏好摘要（無則顯示「還沒有足夠資料」）
- 顯示 top 5 分類權重
- 提示用戶可以直接在 DM 裡說出偏好

### 5. 前端「我的偏好」頁面
- 路徑：`/app/preferences`（或設定頁面的新 tab）
- 顯示 preference_summary（可編輯 textarea）
- 顯示分類權重（唯讀條狀圖）
- 儲存按鈕呼叫 PATCH /api/preferences/summary
