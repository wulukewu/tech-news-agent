# 聊天記錄持久化與跨平台同步設計

## 概述

這份文件設計了一個完整的聊天記錄持久化系統，支援 Web 界面和 Discord 之間的無縫對話同步，讓用戶可以在任何平台上繼續之前的對話。

## 核心功能需求

### 1. 對話持久化

- ✅ 所有對話自動儲存到資料庫
- ✅ 支援對話標題自動生成（基於首次問題）
- ✅ 對話分類和標籤系統
- ✅ 對話搜尋功能（按內容、時間、標籤）

### 2. 跨平台同步

- ✅ Web 界面和 Discord 共享同一套對話資料
- ✅ 平台間無縫切換（在 Web 開始，Discord 繼續）
- ✅ 統一的用戶身份識別系統
- ✅ 即時同步更新

### 3. 用戶體驗

- ✅ 對話列表界面（最近對話、收藏對話）
- ✅ 對話歷史查看和搜尋
- ✅ 對話分享和匯出功能
- ✅ 對話刪除和歸檔

## 資料庫設計

### 擴展現有的 conversations 表

```sql
-- 擴展對話表，加入更多元資料
ALTER TABLE conversations ADD COLUMN IF NOT EXISTS title VARCHAR(200);
ALTER TABLE conversations ADD COLUMN IF NOT EXISTS platform VARCHAR(20) DEFAULT 'web'; -- 'web', 'discord'
ALTER TABLE conversations ADD COLUMN IF NOT EXISTS is_archived BOOLEAN DEFAULT FALSE;
ALTER TABLE conversations ADD COLUMN IF NOT EXISTS is_favorite BOOLEAN DEFAULT FALSE;
ALTER TABLE conversations ADD COLUMN IF NOT EXISTS tags JSONB DEFAULT '[]';
ALTER TABLE conversations ADD COLUMN IF NOT EXISTS summary TEXT;
ALTER TABLE conversations ADD COLUMN IF NOT EXISTS last_message_at TIMESTAMP DEFAULT NOW();

-- 建立索引
CREATE INDEX IF NOT EXISTS idx_conversations_user_platform ON conversations(user_id, platform);
CREATE INDEX IF NOT EXISTS idx_conversations_last_message ON conversations(last_message_at DESC);
CREATE INDEX IF NOT EXISTS idx_conversations_title_search ON conversations USING gin(to_tsvector('english', title));
```

### 新增對話訊息表（詳細記錄）

```sql
CREATE TABLE IF NOT EXISTS conversation_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID REFERENCES conversations(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL, -- 'user', 'assistant'
    content TEXT NOT NULL,
    metadata JSONB DEFAULT '{}', -- 儲存額外資訊如文章連結、圖片等
    platform VARCHAR(20) NOT NULL, -- 'web', 'discord'
    created_at TIMESTAMP DEFAULT NOW(),

    CONSTRAINT valid_role CHECK (role IN ('user', 'assistant')),
    CONSTRAINT valid_platform CHECK (platform IN ('web', 'discord'))
);

CREATE INDEX idx_messages_conversation_id ON conversation_messages(conversation_id);
CREATE INDEX idx_messages_created_at ON conversation_messages(created_at DESC);
```

### 用戶平台綁定表

```sql
CREATE TABLE IF NOT EXISTS user_platform_links (
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    platform VARCHAR(20) NOT NULL,
    platform_user_id VARCHAR(100) NOT NULL, -- Discord user ID, Web user ID 等
    platform_username VARCHAR(100),
    linked_at TIMESTAMP DEFAULT NOW(),

    PRIMARY KEY (user_id, platform),
    UNIQUE (platform, platform_user_id)
);
```

## API 設計

### 對話管理 API

```typescript
// 對話列表
GET /api/conversations
Query: {
  page?: number
  limit?: number
  platform?: 'web' | 'discord' | 'all'
  archived?: boolean
  search?: string
  tags?: string[]
}

Response: {
  conversations: Array<{
    id: string
    title: string
    summary: string
    platform: string
    lastMessageAt: string
    messageCount: number
    tags: string[]
    isFavorite: boolean
    isArchived: boolean
  }>
  total: number
  hasMore: boolean
}

// 建立新對話
POST /api/conversations
Body: {
  platform: 'web' | 'discord'
  initialMessage?: string
  title?: string
}

// 取得對話詳情
GET /api/conversations/{id}
Response: {
  id: string
  title: string
  summary: string
  platform: string
  tags: string[]
  messages: Array<{
    id: string
    role: 'user' | 'assistant'
    content: string
    metadata: object
    platform: string
    createdAt: string
  }>
  createdAt: string
  lastMessageAt: string
}

// 繼續對話
POST /api/conversations/{id}/messages
Body: {
  content: string
  platform: 'web' | 'discord'
}

// 更新對話元資料
PATCH /api/conversations/{id}
Body: {
  title?: string
  tags?: string[]
  isFavorite?: boolean
  isArchived?: boolean
}

// 刪除對話
DELETE /api/conversations/{id}

// 搜尋對話
GET /api/conversations/search
Query: {
  q: string
  platform?: string
  dateFrom?: string
  dateTo?: string
}
```

### 跨平台同步 API

```typescript
// 綁定平台帳號
POST /api/user/platforms
Body: {
  platform: 'discord'
  platformUserId: string
  platformUsername?: string
}

// 取得用戶的平台綁定
GET /api/user/platforms

// 同步對話到其他平台
POST /api/conversations/{id}/sync
Body: {
  targetPlatform: 'web' | 'discord'
}
```

## 前端界面設計

### 1. 對話列表頁面 (`/chat`)

```tsx
// 主要功能
- 對話列表（按時間排序）
- 搜尋和篩選
- 新增對話按鈕
- 對話預覽（標題、最後訊息、時間）
- 收藏和歸檔功能
- 平台標籤顯示
```

### 2. 對話詳情頁面 (`/chat/[id]`)

```tsx
// 主要功能
- 完整對話歷史
- 繼續對話輸入框
- 對話設定（標題、標籤、收藏）
- 分享和匯出功能
- 跨平台同步狀態顯示
```

### 3. 對話搜尋頁面 (`/chat/search`)

```tsx
// 主要功能
- 全文搜尋
- 進階篩選（時間、平台、標籤）
- 搜尋結果高亮
- 快速跳轉到對話
```

## Discord Bot 整合

### 1. 用戶身份識別

```python
# Discord Bot 需要能夠識別用戶並連結到系統用戶
async def link_discord_user(discord_user_id: str, system_user_id: str):
    # 建立 Discord 用戶與系統用戶的連結
    pass

async def get_system_user_from_discord(discord_user_id: str) -> Optional[str]:
    # 從 Discord ID 取得系統用戶 ID
    pass
```

### 2. 對話同步

```python
# Discord Bot 指令
@bot.command(name='continue')
async def continue_conversation(ctx, conversation_id: str):
    """在 Discord 中繼續 Web 上的對話"""
    pass

@bot.command(name='conversations')
async def list_conversations(ctx):
    """列出用戶的對話列表"""
    pass

@bot.command(name='search')
async def search_conversations(ctx, *, query: str):
    """搜尋對話歷史"""
    pass
```

### 3. 自動對話建立

```python
# 當用戶在 Discord 中提問時，自動建立或繼續對話
@bot.event
async def on_message(message):
    if message.author.bot:
        return

    # 檢查是否為 QA 問題
    if is_qa_question(message.content):
        # 取得或建立對話
        conversation = await get_or_create_conversation(
            discord_user_id=str(message.author.id),
            platform='discord'
        )

        # 處理問題並回應
        response = await process_qa_query(
            conversation_id=conversation.id,
            query=message.content,
            platform='discord'
        )

        await message.reply(response)
```

## 實作優先順序

### Phase 1: 基礎持久化（1-2 週）

1. ✅ 擴展資料庫 schema
2. ✅ 實作對話 CRUD API
3. ✅ 基礎前端對話列表和詳情頁面
4. ✅ 整合現有 QA Agent

### Phase 2: 跨平台同步（1 週）

1. ✅ 用戶平台綁定系統
2. ✅ Discord Bot 基礎整合
3. ✅ 跨平台對話同步 API
4. ✅ 前端平台狀態顯示

### Phase 3: 進階功能（1 週）

1. ✅ 對話搜尋和篩選
2. ✅ 對話分享和匯出
3. ✅ 自動標題生成
4. ✅ 對話分析和洞察

## 技術考量

### 1. 效能優化

- 對話列表分頁載入
- 訊息內容壓縮儲存
- 快取熱門對話
- 資料庫查詢優化

### 2. 資料安全

- 對話內容加密
- 用戶隱私保護
- 跨平台身份驗證
- 資料備份和恢復

### 3. 擴展性

- 支援更多平台（Telegram、Slack 等）
- 對話匯入/匯出格式標準化
- API 版本控制
- 微服務架構準備

## 用戶體驗流程

### 場景 1: Web 開始，Discord 繼續

1. 用戶在 Web 界面提問並獲得回答
2. 用戶切換到 Discord
3. 使用 `/continue <conversation_id>` 或直接提問
4. Bot 識別用戶並繼續同一對話
5. 對話歷史在兩個平台同步顯示

### 場景 2: 對話管理

1. 用戶查看對話列表
2. 搜尋特定主題的歷史對話
3. 收藏重要對話
4. 分享對話給其他人
5. 匯出對話作為文件

### 場景 3: 智能功能

1. 系統自動生成對話標題
2. 根據對話內容建議標籤
3. 推薦相關的歷史對話
4. 分析用戶問答模式

## 結論

這個設計提供了完整的聊天記錄持久化和跨平台同步解決方案，確保用戶可以在任何平台上無縫地繼續對話。重點是：

1. **統一的資料模型**：所有平台共享同一套對話資料
2. **靈活的 API 設計**：支援各種對話管理需求
3. **良好的用戶體驗**：直觀的界面和智能功能
4. **可擴展的架構**：易於添加新平台和功能

這確實比 roadmap 上的其他功能更重要，因為它是所有 AI Agent 功能的基礎設施。
