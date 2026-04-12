# Discord Bot Cog Architecture

**Visual representation of cog responsibilities and interactions**

---

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Discord User                             │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             │ Slash Commands & Button Clicks
                             │
┌────────────────────────────▼────────────────────────────────────┐
│                      Discord Bot (TechNewsBot)                   │
│                                                                   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                    Command Layer                         │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │   │
│  │  │AdminCommands │  │NewsCommands  │  │Subscription  │  │   │
│  │  │              │  │              │  │Commands      │  │   │
│  │  └──────────────┘  └──────────────┘  └──────────────┘  │   │
│  │  ┌──────────────┐  ┌──────────────┐                     │   │
│  │  │ReadingList   │  │Notification  │                     │   │
│  │  │Cog           │  │Settings      │                     │   │
│  │  └──────────────┘  └──────────────┘                     │   │
│  └─────────────────────────────────────────────────────────┘   │
│                             │                                    │
│  ┌─────────────────────────▼────────────────────────────────┐  │
│  │                  UI Component Layer                       │  │
│  │  ┌──────────────┐              ┌──────────────┐          │  │
│  │  │Interactions  │              │Persistent    │          │  │
│  │  │Cog           │              │Views         │          │  │
│  │  │(Non-persist) │              │(Persistent)  │          │  │
│  │  └──────────────┘              └──────────────┘          │  │
│  └─────────────────────────────────────────────────────────┘   │
│                             │                                    │
└─────────────────────────────┼────────────────────────────────────┘
                              │
                              │ Service Calls
                              │
┌─────────────────────────────▼────────────────────────────────────┐
│                        Service Layer                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐           │
│  │Supabase      │  │LLM           │  │RSS           │           │
│  │Service       │  │Service       │  │Service       │           │
│  └──────────────┘  └──────────────┘  └──────────────┘           │
│  ┌──────────────┐  ┌──────────────┐                             │
│  │DM            │  │Scheduler     │                             │
│  │Notification  │  │              │                             │
│  └──────────────┘  └──────────────┘                             │
└───────────────────────────────────────────────────────────────────┘
                              │
                              │ Database Operations
                              │
┌─────────────────────────────▼────────────────────────────────────┐
│                    Supabase Database                              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐         │
│  │users     │  │feeds     │  │articles  │  │reading   │         │
│  │          │  │          │  │          │  │_list     │         │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘         │
│  ┌──────────┐  ┌──────────┐                                      │
│  │user_     │  │analytics │                                      │
│  │subscript.│  │_events   │                                      │
│  └──────────┘  └──────────┘                                      │
└───────────────────────────────────────────────────────────────────┘
```

---

## Cog Interaction Map

```
                    ┌─────────────────┐
                    │  AdminCommands  │
                    │                 │
                    │ /trigger_fetch  │
                    │ /scheduler_     │
                    │  status         │
                    └────────┬────────┘
                             │
                             │ Calls
                             │
                    ┌────────▼────────┐
                    │   Scheduler     │
                    │   (tasks/)      │
                    └─────────────────┘


┌─────────────────┐         ┌─────────────────┐         ┌─────────────────┐
│ Subscription    │         │  NewsCommands   │         │  ReadingList    │
│ Commands        │         │                 │         │  Cog            │
│                 │         │  /news_now      │         │                 │
│ /add_feed       │────────▶│                 │◀────────│ /reading_list   │
│ /list_feeds     │ Queries │  Uses views     │ Shares  │  view           │
│ /unsubscribe_   │ subs    │  from           │ data    │ /reading_list   │
│  feed           │         │  Interactions   │         │  recommend      │
└────────┬────────┘         └────────┬────────┘         └────────┬────────┘
         │                           │                           │
         │                           │                           │
         │                  ┌────────▼────────┐                  │
         │                  │ InteractionsCog │                  │
         │                  │                 │                  │
         │                  │ ReadLaterButton │                  │
         │                  │ FilterSelect    │                  │
         │                  │ DeepDiveButton  │                  │
         │                  │ MarkReadButton  │                  │
         │                  └────────┬────────┘                  │
         │                           │                           │
         │                           │ Persistent                │
         │                           │ versions                  │
         │                           │                           │
         │                  ┌────────▼────────┐                  │
         │                  │ PersistentViews │                  │
         │                  │                 │                  │
         │                  │ Persistent*     │                  │
         │                  │ (survives       │                  │
         │                  │  restarts)      │                  │
         │                  └────────┬────────┘                  │
         │                           │                           │
         └───────────────────────────┼───────────────────────────┘
                                     │
                                     │ All call
                                     │
                            ┌────────▼────────┐
                            │ SupabaseService │
                            │                 │
                            │ Database ops    │
                            └─────────────────┘


┌─────────────────┐
│ Notification    │
│ Settings        │
│                 │
│ /notifications  │
│ /notification_  │
│  status         │
└────────┬────────┘
         │
         │ Updates
         │ preferences
         │
         ▼
┌─────────────────┐
│ DM Notification │
│ Service         │
│                 │
│ Sends DMs       │
└─────────────────┘
```

---

## Component Dependency Graph

```
┌─────────────────────────────────────────────────────────────────┐
│                         Cog Dependencies                         │
└─────────────────────────────────────────────────────────────────┘

AdminCommands
  └─→ app.tasks.scheduler
      ├─→ background_fetch_job()
      └─→ get_scheduler_health()

NewsCommands
  ├─→ SupabaseService
  │   ├─→ get_or_create_user()
  │   ├─→ get_user_subscriptions()
  │   └─→ query articles
  └─→ InteractionsCog (imports views)
      ├─→ ReadLaterView
      ├─→ FilterView
      └─→ DeepDiveView

InteractionsCog
  ├─→ SupabaseService
  │   ├─→ save_to_reading_list()
  │   ├─→ update_article_status()
  │   └─→ update_article_rating()
  └─→ LLMService
      └─→ generate_deep_dive()

PersistentViews
  ├─→ SupabaseService
  │   ├─→ save_to_reading_list()
  │   ├─→ update_article_status()
  │   ├─→ update_article_rating()
  │   └─→ query articles (for deep dive)
  └─→ LLMService
      └─→ generate_deep_dive()

ReadingListCog
  ├─→ SupabaseService
  │   ├─→ get_reading_list()
  │   ├─→ get_highly_rated_articles()
  │   ├─→ update_article_status()
  │   └─→ update_article_rating()
  ├─→ LLMService
  │   └─→ generate_reading_recommendation()
  └─→ app.bot.utils.validators
      └─→ validate_rating()

SubscriptionCommands
  ├─→ SupabaseService
  │   ├─→ subscribe_to_feed()
  │   ├─→ get_user_subscriptions()
  │   └─→ unsubscribe_from_feed()
  └─→ app.bot.utils.decorators
      └─→ ensure_user_registered

NotificationSettings
  └─→ SupabaseService
      ├─→ update_notification_settings()
      └─→ get_notification_settings()
```

---

## Data Flow Examples

### Example 1: User Subscribes to Feed

```
User: /add_feed name="TechCrunch" url="..." category="Tech"
  │
  ├─→ SubscriptionCommands.add_feed()
  │     │
  │     ├─→ validate_and_sanitize_feed_data()
  │     │     └─→ Returns: {name, url, category} (sanitized)
  │     │
  │     ├─→ ensure_user_registered()
  │     │     └─→ SupabaseService.get_or_create_user()
  │     │           └─→ Returns: user_uuid
  │     │
  │     ├─→ SupabaseService.client.table('feeds').select()
  │     │     └─→ Check if feed exists
  │     │
  │     ├─→ SupabaseService.client.table('feeds').insert()
  │     │     └─→ Create feed if not exists
  │     │
  │     └─→ SupabaseService.subscribe_to_feed()
  │           └─→ INSERT into user_subscriptions
  │
  └─→ Response: "✅ 已成功訂閱 TechCrunch (Tech)"
```

### Example 2: User Views Personalized News

```
User: /news_now
  │
  ├─→ NewsCommands.news_now()
  │     │
  │     ├─→ ensure_user_registered()
  │     │     └─→ SupabaseService.get_or_create_user()
  │     │
  │     ├─→ SupabaseService.get_user_subscriptions()
  │     │     └─→ Returns: [sub1, sub2, sub3]
  │     │
  │     ├─→ SupabaseService.client.table('articles').select()
  │     │     └─→ Filter by feed_ids, published_at, tinkering_index
  │     │     └─→ Returns: [article1, article2, ...]
  │     │
  │     ├─→ Build notification message
  │     │     └─→ Group by category, format with emojis
  │     │
  │     └─→ Create interactive views
  │           ├─→ FilterView(articles)
  │           ├─→ DeepDiveView(articles[:5])
  │           └─→ ReadLaterView(articles[:10])
  │
  └─→ Response: Message with articles + interactive buttons
```

### Example 3: User Clicks "Read Later" Button

```
User: Clicks "⭐ Read Later" button
  │
  ├─→ InteractionsCog.ReadLaterButton.callback()
  │     │
  │     ├─→ interaction.response.defer(ephemeral=True)
  │     │
  │     ├─→ SupabaseService.save_to_reading_list()
  │     │     └─→ INSERT into reading_list
  │     │           (user_id, article_id, status='Unread')
  │     │
  │     ├─→ self.disabled = True
  │     │
  │     ├─→ interaction.message.edit(view=self.view)
  │     │     └─→ Update message to show disabled button
  │     │
  │     └─→ interaction.followup.send()
  │           └─→ "✅ 已加入閱讀清單！"
  │
  └─→ Button becomes disabled, user sees confirmation
```

### Example 4: Bot Restarts, User Clicks Persistent Button

```
Bot restarts (all in-memory state lost)
  │
User: Clicks persistent "⭐ Read Later" button
  │
  ├─→ PersistentViews.PersistentReadLaterButton.callback()
  │     │
  │     ├─→ custom_id = interaction.data.get('custom_id')
  │     │     └─→ "read_later_123e4567-e89b-12d3-a456-426614174000"
  │     │
  │     ├─→ parse_article_id_from_custom_id()
  │     │     └─→ Returns: UUID("123e4567-e89b-12d3-a456-426614174000")
  │     │
  │     ├─→ SupabaseService.save_to_reading_list()
  │     │     └─→ INSERT into reading_list
  │     │
  │     ├─→ log_persistent_interaction()
  │     │     └─→ Log post-restart interaction
  │     │
  │     └─→ interaction.followup.send()
  │           └─→ "✅ 已加入閱讀清單！"
  │
  └─→ Button works even after bot restart!
```

---

## Responsibility Decision Tree

```
┌─────────────────────────────────────────────────────────────────┐
│ "Where should this functionality go?"                            │
└─────────────────────────────────────────────────────────────────┘

Is it a slash command?
  ├─ YES → Is it system/admin related?
  │   ├─ YES → AdminCommands
  │   └─ NO → Is it about subscriptions?
  │       ├─ YES → SubscriptionCommands
  │       └─ NO → Is it about reading list?
  │           ├─ YES → ReadingListCog
  │           └─ NO → Is it about notifications?
  │               ├─ YES → NotificationSettings
  │               └─ NO → Is it about news delivery?
  │                   ├─ YES → NewsCommands
  │                   └─ NO → Create new cog
  │
  └─ NO → Is it a UI component (button/select)?
      ├─ YES → Does it need to survive bot restarts?
      │   ├─ YES → PersistentViews
      │   └─ NO → InteractionsCog
      │
      └─ NO → Is it business logic?
          ├─ YES → Move to Service Layer
          └─ NO → Is it a utility function?
              ├─ YES → app.bot.utils
              └─ NO → Reconsider design
```

---

## Testing Strategy by Layer

### Command Layer Tests

```python
# Test slash command responses
async def test_add_feed_success():
    # Mock SupabaseService
    # Call add_feed command
    # Assert success message sent

async def test_add_feed_invalid_url():
    # Call add_feed with invalid URL
    # Assert error message sent
```

### UI Component Layer Tests

```python
# Test button callbacks
async def test_read_later_button_callback():
    # Mock SupabaseService.save_to_reading_list
    # Simulate button click
    # Assert service called with correct params
    # Assert button disabled

async def test_persistent_button_after_restart():
    # Simulate bot restart (no in-memory state)
    # Mock custom_id parsing
    # Simulate button click
    # Assert service called correctly
```

### Service Layer Tests

```python
# Test service methods
async def test_save_to_reading_list():
    # Mock Supabase client
    # Call save_to_reading_list
    # Assert correct INSERT query
    # Assert error handling
```

---

## Conclusion

This architecture provides:

1. **Clear Separation**: Commands, UI components, and services are distinct
2. **Reusability**: UI components can be used across multiple commands
3. **Persistence**: Persistent views survive bot restarts
4. **Testability**: Each layer can be tested independently
5. **Maintainability**: Clear boundaries make changes easier

**Key Principles:**

- Commands orchestrate, don't implement
- UI components handle interactions, don't contain business logic
- Services contain business logic, are stateless and reusable
- Persistent views handle state reconstruction after restarts
