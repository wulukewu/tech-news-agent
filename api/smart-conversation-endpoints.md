# Smart Conversation API Endpoints

This document describes the intelligent conversation features API endpoints that provide auto title generation, summary generation, related conversation recommendations, and conversation insights.

**Validates: Task 7.1 - Auto Title Generation Service Implementation**
**Requirements: 3.2, 3.5, 6.1, 6.2, 6.3, 6.4, 6.5**

## Overview

The Smart Conversation API provides intelligent features built on top of the core conversation persistence system:

- **Auto Title Generation** - Generates concise, meaningful titles from conversation content
- **Summary Generation** - Creates summaries and extracts key insights from conversations
- **Related Conversations** - Finds topically similar conversations based on tags and keywords
- **Conversation Insights** - Analyzes conversation patterns and provides learning suggestions

All endpoints use the Groq-backed LLM service for intelligent content generation.

## Authentication

All endpoints require JWT authentication via the `Authorization: Bearer <token>` header.

## Endpoints

### 1. Generate Conversation Title

**POST** `/api/conversations/{conversation_id}/generate-title`

Generates an intelligent title for a conversation based on its first few messages. The title is generated in the same language as the conversation (Chinese or English).

#### Parameters

| Parameter         | Type          | Location | Required | Description                                           |
| ----------------- | ------------- | -------- | -------- | ----------------------------------------------------- |
| `conversation_id` | string (UUID) | path     | Yes      | ID of the conversation                                |
| `persist`         | boolean       | query    | No       | Whether to save the title to database (default: true) |

#### Request Example

```bash
curl -X POST "https://api.example.com/api/conversations/123e4567-e89b-12d3-a456-426614174000/generate-title?persist=true" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

#### Response Example

```json
{
  "success": true,
  "data": {
    "title": "FastAPI Authentication Implementation",
    "persisted": true,
    "conversation_id": "123e4567-e89b-12d3-a456-426614174000"
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

#### Features

- ✅ **Multi-language support**: Automatically detects and uses the conversation's language
- ✅ **Title optimization**: Removes quotes, extra whitespace, and formatting
- ✅ **Deduplication logic**: Generates unique, descriptive titles
- ✅ **User confirmation**: `persist=false` allows preview before saving
- ✅ **Fallback handling**: Returns "New Conversation" if no messages exist

#### Error Responses

- `404 Not Found` - Conversation not found or user doesn't have access
- `500 Internal Server Error` - LLM service failure or database error

---

### 2. Generate Conversation Summary

**POST** `/api/conversations/{conversation_id}/generate-summary`

Generates a concise summary (≤150 words) and 2-3 key insights from the conversation.

#### Parameters

| Parameter         | Type          | Location | Required | Description                                             |
| ----------------- | ------------- | -------- | -------- | ------------------------------------------------------- |
| `conversation_id` | string (UUID) | path     | Yes      | ID of the conversation                                  |
| `persist`         | boolean       | query    | No       | Whether to save the summary to database (default: true) |

#### Request Example

```bash
curl -X POST "https://api.example.com/api/conversations/123e4567-e89b-12d3-a456-426614174000/generate-summary" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

#### Response Example

```json
{
  "success": true,
  "data": {
    "summary": "Discussion about Python async/await syntax and usage patterns. The conversation covered basic concepts and practical implementation examples.\n\n• Async/await enables non-blocking I/O operations\n• FastAPI provides built-in async support\n• Proper error handling is crucial in async code",
    "persisted": true,
    "conversation_id": "123e4567-e89b-12d3-a456-426614174000"
  },
  "timestamp": "2024-01-15T10:35:00Z"
}
```

---

### 3. Get Related Conversations

**GET** `/api/conversations/{conversation_id}/related`

Finds conversations related to the given one based on tag overlap and keyword similarity.

#### Parameters

| Parameter         | Type          | Location | Required | Description                                         |
| ----------------- | ------------- | -------- | -------- | --------------------------------------------------- |
| `conversation_id` | string (UUID) | path     | Yes      | ID of the reference conversation                    |
| `limit`           | integer       | query    | No       | Max number of recommendations (default: 5, max: 20) |

#### Request Example

```bash
curl -X GET "https://api.example.com/api/conversations/123e4567-e89b-12d3-a456-426614174000/related?limit=5" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

#### Response Example

```json
{
  "success": true,
  "data": [
    {
      "conversation_id": "234e5678-e89b-12d3-a456-426614174001",
      "title": "FastAPI Async Endpoints",
      "similarity_score": 0.8542,
      "shared_tags": ["python", "async", "fastapi"],
      "reason": "Shares tags: #python, #async, #fastapi; 3 overlapping topic keyword(s)"
    },
    {
      "conversation_id": "345e6789-e89b-12d3-a456-426614174002",
      "title": "Python Async Programming Basics",
      "similarity_score": 0.7231,
      "shared_tags": ["python", "async"],
      "reason": "Shares tags: #python, #async; 2 overlapping topic keyword(s)"
    }
  ],
  "timestamp": "2024-01-15T10:40:00Z"
}
```

#### Similarity Score

The `similarity_score` is a normalized value between 0 and 1:

- **0.6 weight**: Tag overlap (shared tags / total unique tags)
- **0.4 weight**: Keyword overlap (shared keywords / total unique keywords)

Higher scores indicate stronger topical similarity.

---

### 4. Get Conversation Insights

**GET** `/api/conversations/insights`

Analyzes the user's conversation history and generates personalized insights, including topic distribution, activity metrics, knowledge gaps, and learning suggestions.

#### Parameters

| Parameter | Type    | Location | Required | Description                                      |
| --------- | ------- | -------- | -------- | ------------------------------------------------ |
| `days`    | integer | query    | No       | Look-back window in days (default: 30, max: 365) |

#### Request Example

```bash
curl -X GET "https://api.example.com/api/conversations/insights?days=30" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

#### Response Example

```json
{
  "success": true,
  "data": {
    "topic_distribution": {
      "python": 15,
      "async": 12,
      "fastapi": 8,
      "javascript": 5
    },
    "active_days": 18,
    "avg_messages_per_day": 8.5,
    "top_tags": ["python", "async", "fastapi", "web-development"],
    "knowledge_gaps": [
      "Error handling in async code",
      "Testing async functions",
      "Performance optimization"
    ],
    "interest_areas": ["python", "async", "fastapi", "web-development", "api-design"],
    "learning_suggestions": [
      "Practice implementing error handling in async/await code",
      "Learn about pytest-asyncio for testing async functions",
      "Explore FastAPI's dependency injection system",
      "Study API design best practices and RESTful principles"
    ],
    "trend_summary": "You're actively learning Python with a strong focus on asynchronous programming and web development. Your conversations show consistent engagement with FastAPI and modern Python patterns. Consider deepening your knowledge in testing and error handling to build more robust applications.",
    "generated_at": "2024-01-15T10:45:00Z"
  },
  "timestamp": "2024-01-15T10:45:00Z"
}
```

#### Insights Breakdown

- **topic_distribution**: Count of conversations per topic/tag
- **active_days**: Number of distinct days with conversation activity
- **avg_messages_per_day**: Average messages sent per active day
- **top_tags**: Most frequently used tags across conversations
- **knowledge_gaps**: Topics where understanding appears incomplete (LLM-inferred)
- **interest_areas**: Topics with highest engagement
- **learning_suggestions**: Personalized next-step recommendations (LLM-generated)
- **trend_summary**: Human-readable analysis of learning patterns (LLM-generated)

---

## Implementation Details

### Service Architecture

All endpoints use the `SmartConversationService` which depends on:

- **ConversationRepository**: For conversation metadata access
- **MessageRepository**: For message content access
- **AsyncOpenAI Client**: For LLM calls (Groq API)

### LLM Configuration

- **Fast Model**: `llama-3.1-8b-instant` (for title generation)
- **Smart Model**: `llama-3.3-70b-versatile` (for summaries and insights)
- **Timeout**: 30 seconds
- **Max Retries**: 2 with exponential backoff (2s, 4s)

### Performance Characteristics

| Operation             | Target Latency | Notes                            |
| --------------------- | -------------- | -------------------------------- |
| Title Generation      | < 3s           | Samples first 6 messages         |
| Summary Generation    | < 5s           | Samples up to 40 messages        |
| Related Conversations | < 500ms        | Lightweight keyword/tag matching |
| Insights Analysis     | < 10s          | Analyzes up to 100 conversations |

### Error Handling

All endpoints implement:

- ✅ Ownership verification (users can only access their own conversations)
- ✅ LLM retry logic with exponential backoff
- ✅ Graceful degradation (partial results on LLM failure)
- ✅ Detailed error logging for debugging

---

## Usage Examples

### Workflow 1: Auto-generate Title on Conversation Creation

```javascript
// 1. Create a new conversation
const createResponse = await fetch('/api/conversations', {
  method: 'POST',
  headers: {
    Authorization: `Bearer ${token}`,
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    title: 'Temporary Title',
    platform: 'web',
  }),
});
const { data: conversation } = await createResponse.json();

// 2. Add initial messages
await fetch(`/api/conversations/${conversation.id}/messages`, {
  method: 'POST',
  headers: {
    Authorization: `Bearer ${token}`,
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    role: 'user',
    content: 'How do I implement authentication in FastAPI?',
  }),
});

// 3. Generate intelligent title after a few messages
const titleResponse = await fetch(
  `/api/conversations/${conversation.id}/generate-title?persist=true`,
  {
    method: 'POST',
    headers: { Authorization: `Bearer ${token}` },
  }
);
const { data: titleData } = await titleResponse.json();
console.log('Generated title:', titleData.title);
```

### Workflow 2: Preview Title Before Saving

```javascript
// Generate title without persisting
const previewResponse = await fetch(
  `/api/conversations/${conversationId}/generate-title?persist=false`,
  {
    method: 'POST',
    headers: { Authorization: `Bearer ${token}` },
  }
);
const { data } = await previewResponse.json();

// Show to user for confirmation
if (confirm(`Use this title: "${data.title}"?`)) {
  // User confirmed - update manually
  await fetch(`/api/conversations/${conversationId}`, {
    method: 'PATCH',
    headers: {
      Authorization: `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ title: data.title }),
  });
}
```

### Workflow 3: Show Related Conversations in Sidebar

```javascript
// Get related conversations for current conversation
const relatedResponse = await fetch(`/api/conversations/${currentConversationId}/related?limit=5`, {
  headers: { Authorization: `Bearer ${token}` },
});
const { data: related } = await relatedResponse.json();

// Display in sidebar
related.forEach((conv) => {
  console.log(`${conv.title} (${conv.similarity_score.toFixed(2)})`);
  console.log(`  Reason: ${conv.reason}`);
});
```

---

## Testing

Comprehensive test suite available at `backend/tests/services/test_smart_conversation.py`:

- ✅ English conversation title generation
- ✅ Chinese conversation title generation
- ✅ Title sanitization (quote removal)
- ✅ Persist vs. preview mode
- ✅ Empty conversation handling
- ✅ LLM failure retry logic
- ✅ Summary generation
- ✅ Related conversation recommendation
- ✅ Conversation insights analysis
- ✅ Full integration workflow

Run tests:

```bash
cd backend
python3 -m pytest tests/services/test_smart_conversation.py -v
```

---

## Future Enhancements

Potential improvements for future iterations:

1. **Batch Title Generation**: Generate titles for multiple conversations in one request
2. **Custom Prompts**: Allow users to customize title generation style
3. **Title History**: Track title changes and allow rollback
4. **Semantic Search**: Use vector embeddings for more accurate related conversations
5. **Real-time Insights**: Stream insights as they're generated
6. **Export Insights**: Download insights as PDF or markdown report

---

## Related Documentation

- [Conversation API Reference](./conversations.md)
- [Smart Conversation Service Implementation](../../backend/app/services/smart_conversation.py)
- [Task 7.1 Specification](.kiro/specs/chat-persistence-system/tasks.md#71)
- [Requirements Document](.kiro/specs/chat-persistence-system/requirements.md)

---

**Last Updated**: 2024-01-15
**API Version**: 1.0
**Status**: ✅ Implemented and Tested
