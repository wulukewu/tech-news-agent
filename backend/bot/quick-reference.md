# Discord Bot Cog Quick Reference

**Quick lookup guide for developers working with Discord bot cogs**

---

## When to Use Each Cog

| Need to...                   | Use Cog                | Example                     |
| ---------------------------- | ---------------------- | --------------------------- |
| Trigger scheduler manually   | `AdminCommands`        | `/trigger_fetch`            |
| Check scheduler health       | `AdminCommands`        | `/scheduler_status`         |
| Show personalized news       | `NewsCommands`         | `/news_now`                 |
| Subscribe to RSS feed        | `SubscriptionCommands` | `/add_feed`                 |
| List user subscriptions      | `SubscriptionCommands` | `/list_feeds`               |
| Unsubscribe from feed        | `SubscriptionCommands` | `/unsubscribe_feed`         |
| View reading list            | `ReadingListCog`       | `/reading_list view`        |
| Get AI recommendations       | `ReadingListCog`       | `/reading_list recommend`   |
| Enable/disable notifications | `NotificationSettings` | `/notifications`            |
| Check notification status    | `NotificationSettings` | `/notification_status`      |
| Add interactive button       | `InteractionsCog`      | `ReadLaterButton`           |
| Add persistent button        | `PersistentViews`      | `PersistentReadLaterButton` |

---

## Component Selection Guide

### When to Use InteractionsCog Components

✅ **Use when:**

- Button/select is part of a command response
- Component lifetime is tied to message lifetime
- No need to survive bot restarts
- Timeout is acceptable (default: 180 seconds)

**Examples:**

- `ReadLaterButton` in `/news_now` response
- `FilterSelect` for filtering articles
- `DeepDiveButton` for AI analysis

### When to Use PersistentViews Components

✅ **Use when:**

- Component must survive bot restarts
- Long-lived messages (e.g., pinned messages)
- No timeout desired (`timeout=None`)
- State can be reconstructed from `custom_id`

**Examples:**

- `PersistentReadLaterButton` in scheduled DM notifications
- `PersistentMarkReadButton` in persistent reading list
- `PersistentRatingSelect` for long-term rating collection

---

## Common Patterns

### Pattern 1: Add a New Slash Command

```python
# 1. Choose the appropriate cog based on responsibility
# 2. Add command to cog class

@app_commands.command(name="my_command", description="Description")
@app_commands.describe(param="Parameter description")
async def my_command(self, interaction: discord.Interaction, param: str):
    """Command implementation"""
    await interaction.response.defer(ephemeral=True)

    try:
        # 1. Validate input
        # 2. Call service layer
        # 3. Format response
        # 4. Send response
        await interaction.followup.send("✅ Success!", ephemeral=True)
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        await interaction.followup.send("❌ Error", ephemeral=True)
```

### Pattern 2: Add a New Interactive Button

```python
# In InteractionsCog (interactions.py)

class MyButton(discord.ui.Button):
    def __init__(self, article_id: UUID, article_title: str):
        super().__init__(
            style=discord.ButtonStyle.primary,
            label=f"🔥 {article_title[:15]}...",
            custom_id=f"my_action_{article_id}"
        )
        self.article_id = article_id

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        try:
            # Call service layer
            supabase = SupabaseService()
            await supabase.my_service_method(
                str(interaction.user.id),
                self.article_id
            )

            # Disable button
            self.disabled = True
            await interaction.message.edit(view=self.view)

            # Send confirmation
            await interaction.followup.send("✅ Done!", ephemeral=True)

        except Exception as e:
            logger.error(f"Error: {e}", exc_info=True)
            await interaction.followup.send("❌ Error", ephemeral=True)


class MyView(discord.ui.View):
    def __init__(self, articles: List[ArticleSchema]):
        super().__init__(timeout=None)  # or timeout=180
        for article in articles:
            self.add_item(MyButton(article.id, article.title))
```

### Pattern 3: Add a Persistent Button

```python
# In PersistentViews (persistent_views.py)

class PersistentMyButton(discord.ui.Button):
    def __init__(self):
        super().__init__(
            style=discord.ButtonStyle.primary,
            label="🔥 My Action",
            custom_id="my_action_persistent"
        )

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        custom_id = interaction.data.get('custom_id', '')
        discord_id = str(interaction.user.id)

        try:
            # Parse article_id from custom_id
            article_id = parse_article_id_from_custom_id(
                custom_id, 'my_action_'
            )

            # Call service layer
            supabase = SupabaseService()
            await supabase.my_service_method(discord_id, article_id)

            # Send confirmation
            await interaction.followup.send("✅ Done!", ephemeral=True)

            # Log persistent interaction
            log_persistent_interaction(
                user_id=discord_id,
                action='my_action',
                article_id=article_id,
                custom_id=custom_id,
                success=True
            )

        except ValueError as e:
            # Invalid custom_id
            await interaction.followup.send("❌ Invalid ID", ephemeral=True)
        except Exception as e:
            logger.error(f"Error: {e}", exc_info=True)
            await interaction.followup.send("❌ Error", ephemeral=True)


# Register in bot setup_hook (client.py)
my_view = discord.ui.View(timeout=None)
my_view.add_item(PersistentMyButton())
self.add_view(my_view)
```

### Pattern 4: Call Service Layer

```python
# Always use try-except for service calls

try:
    supabase = SupabaseService()
    result = await supabase.my_method(param1, param2)
    # Handle success
except SupabaseServiceError as e:
    # Database-specific error
    logger.error(f"Database error: {e}", exc_info=True)
    await interaction.followup.send("❌ Database error", ephemeral=True)
except Exception as e:
    # Unexpected error
    logger.error(f"Unexpected error: {e}", exc_info=True)
    await interaction.followup.send("❌ Unexpected error", ephemeral=True)
```

---

## Error Handling Best Practices

### 1. Always Defer Long Operations

```python
# ✅ GOOD
@app_commands.command(name="my_command")
async def my_command(self, interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)  # Defer first!
    # ... long operation ...
    await interaction.followup.send("Done!")

# ❌ BAD
@app_commands.command(name="my_command")
async def my_command(self, interaction: discord.Interaction):
    # ... long operation ... (will timeout!)
    await interaction.response.send_message("Done!")
```

### 2. Use Specific Exception Types

```python
# ✅ GOOD
try:
    result = await service.method()
except SupabaseServiceError as e:
    # Handle database errors
    logger.error(f"Database error: {e}")
except LLMServiceError as e:
    # Handle LLM errors
    logger.error(f"LLM error: {e}")
except Exception as e:
    # Handle unexpected errors
    logger.error(f"Unexpected error: {e}")

# ❌ BAD
try:
    result = await service.method()
except Exception as e:
    # Too broad, can't distinguish error types
    logger.error(f"Error: {e}")
```

### 3. Log with Context

```python
# ✅ GOOD
logger.error(
    f"Failed to save article {article_id} for user {user_id}: {e}",
    exc_info=True,
    extra={
        "user_id": user_id,
        "article_id": str(article_id),
        "action": "save_to_reading_list",
        "error_type": type(e).__name__
    }
)

# ❌ BAD
logger.error(f"Error: {e}")
```

### 4. Handle Message Edit Failures Gracefully

```python
# ✅ GOOD
try:
    await interaction.message.edit(view=self.view)
except discord.NotFound:
    # Message was deleted, safe to ignore
    logger.info("Message not found (likely deleted)")
except discord.HTTPException as e:
    # Other Discord API errors
    logger.warning(f"Failed to edit message: {e}")

# ❌ BAD
await interaction.message.edit(view=self.view)  # Can crash!
```

---

## Service Layer Guidelines

### DO ✅

- Call services for all business logic
- Use dependency injection where possible
- Handle service exceptions in cogs
- Log service calls with context
- Keep services stateless

### DON'T ❌

- Implement business logic in cogs
- Create service instances in loops
- Ignore service exceptions
- Mix UI logic with business logic
- Store state in service instances

---

## Testing Checklist

### Before Committing

- [ ] Command responds within 3 seconds (or defers)
- [ ] Error messages are user-friendly
- [ ] Logging includes context (user_id, action, etc.)
- [ ] Service exceptions are caught and handled
- [ ] Button/select callbacks handle message edit failures
- [ ] Persistent components parse custom_id correctly
- [ ] All database operations use service layer
- [ ] No business logic in cog methods

### Integration Testing

- [ ] Test with real Discord bot (dev environment)
- [ ] Test bot restart with persistent components
- [ ] Test error scenarios (database down, LLM timeout)
- [ ] Test with multiple concurrent users
- [ ] Test message timeout scenarios

---

## Common Mistakes to Avoid

### ❌ Mistake 1: Not Deferring Long Operations

```python
# BAD: Will timeout after 3 seconds
@app_commands.command(name="news_now")
async def news_now(self, interaction: discord.Interaction):
    articles = await fetch_articles()  # Takes 5 seconds
    await interaction.response.send_message(articles)  # TIMEOUT!
```

**Fix:** Always defer first

```python
# GOOD
@app_commands.command(name="news_now")
async def news_now(self, interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    articles = await fetch_articles()
    await interaction.followup.send(articles)
```

### ❌ Mistake 2: Implementing Business Logic in Cogs

```python
# BAD: Business logic in cog
@app_commands.command(name="add_feed")
async def add_feed(self, interaction: discord.Interaction, url: str):
    # Validate URL
    if not url.startswith("http"):
        return
    # Parse feed
    feed_data = feedparser.parse(url)
    # Save to database
    supabase.client.table('feeds').insert(feed_data).execute()
```

**Fix:** Delegate to service layer

```python
# GOOD
@app_commands.command(name="add_feed")
async def add_feed(self, interaction: discord.Interaction, url: str):
    await interaction.response.defer(ephemeral=True)

    try:
        # Validate
        is_valid, sanitized, error = validate_and_sanitize_feed_data(
            name, url, category
        )
        if not is_valid:
            await interaction.followup.send(f"❌ {error}", ephemeral=True)
            return

        # Delegate to service
        supabase = SupabaseService()
        await supabase.subscribe_to_feed(user_id, feed_id)

        await interaction.followup.send("✅ Success!", ephemeral=True)
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        await interaction.followup.send("❌ Error", ephemeral=True)
```

### ❌ Mistake 3: Not Handling Message Edit Failures

```python
# BAD: Will crash if message is deleted
async def callback(self, interaction: discord.Interaction):
    self.disabled = True
    await interaction.message.edit(view=self.view)  # Can fail!
```

**Fix:** Handle exceptions

```python
# GOOD
async def callback(self, interaction: discord.Interaction):
    self.disabled = True
    try:
        await interaction.message.edit(view=self.view)
    except discord.NotFound:
        logger.info("Message not found (likely deleted)")
    except discord.HTTPException as e:
        logger.warning(f"Failed to edit message: {e}")
```

### ❌ Mistake 4: Creating Service Instances in Loops

```python
# BAD: Creates new instance for each article
for article in articles:
    supabase = SupabaseService()  # Wasteful!
    await supabase.save_article(article)
```

**Fix:** Reuse service instance

```python
# GOOD
supabase = SupabaseService()
for article in articles:
    await supabase.save_article(article)
```

---

## Quick Debugging Tips

### Issue: Command not showing in Discord

**Check:**

1. Is the cog loaded in `client.py` `setup_hook()`?
2. Did the bot sync commands (`await self.tree.sync()`)?
3. Is the command decorated with `@app_commands.command()`?

### Issue: Button not responding

**Check:**

1. Is the view added to the message?
2. Is the button's `custom_id` unique?
3. Is the callback method defined correctly?
4. Check logs for exceptions

### Issue: Persistent button not working after restart

**Check:**

1. Is the view registered in `setup_hook()` with `timeout=None`?
2. Does the `custom_id` match the parsing logic?
3. Is `parse_article_id_from_custom_id()` working correctly?
4. Check logs for parsing errors

### Issue: Database operation failing

**Check:**

1. Is the service method catching exceptions?
2. Are the parameters correct (types, UUIDs)?
3. Check Supabase logs for query errors
4. Verify database schema matches code

---

## Resources

- **Full Documentation:** `COG_RESPONSIBILITIES.md`
- **Architecture Diagrams:** `COG_ARCHITECTURE.md`
- **Discord.py Docs:** https://discordpy.readthedocs.io/
- **Service Layer:** `backend/app/services/`
- **Utilities:** `backend/app/bot/utils/`

---

## Need Help?

1. Check this quick reference first
2. Read the full documentation (`COG_RESPONSIBILITIES.md`)
3. Review existing cog implementations
4. Check service layer documentation
5. Ask the team!
