# Discord Bot Documentation

**Tech News Agent Discord Bot - Architecture & Responsibilities**

---

## 📚 Documentation Index

This directory contains comprehensive documentation for the Discord bot architecture:

1. **[COG_RESPONSIBILITIES.md](./COG_RESPONSIBILITIES.md)** - Detailed responsibility definitions for each cog
2. **[COG_ARCHITECTURE.md](./COG_ARCHITECTURE.md)** - Visual architecture diagrams and data flow
3. **[QUICK_REFERENCE.md](./QUICK_REFERENCE.md)** - Quick lookup guide for developers

---

## 🎯 Quick Overview

### Bot Structure

The Tech News Agent Discord bot is organized into **7 cogs**, each with a single, well-defined responsibility:

| Cog                      | Responsibility                                 | Key Commands                                    |
| ------------------------ | ---------------------------------------------- | ----------------------------------------------- |
| **AdminCommands**        | System administration & scheduler management   | `/trigger_fetch`, `/scheduler_status`           |
| **NewsCommands**         | Content discovery & personalized news delivery | `/news_now`                                     |
| **SubscriptionCommands** | RSS feed subscription management               | `/add_feed`, `/list_feeds`, `/unsubscribe_feed` |
| **ReadingListCog**       | Reading list management & AI recommendations   | `/reading_list view`, `/reading_list recommend` |
| **NotificationSettings** | User notification preference management        | `/notifications`, `/notification_status`        |
| **InteractionsCog**      | UI component definitions (non-persistent)      | Buttons, Selects, Views                         |
| **PersistentViews**      | UI components that survive bot restarts        | Persistent Buttons, Selects                     |

---

## 🏗️ Architecture Layers

```
┌─────────────────────────────────────────┐
│         Command Layer (Cogs)            │  ← Slash commands
├─────────────────────────────────────────┤
│      UI Component Layer (Views)         │  ← Buttons, Selects
├─────────────────────────────────────────┤
│       Service Layer (Services)          │  ← Business logic
├─────────────────────────────────────────┤
│      Database Layer (Supabase)          │  ← Data persistence
└─────────────────────────────────────────┘
```

**Key Principle:** Each layer delegates to the layer below, never implementing logic that belongs in a lower layer.

---

## 🚀 Getting Started

### For New Developers

1. **Start here:** Read [QUICK_REFERENCE.md](./QUICK_REFERENCE.md) for common patterns
2. **Understand architecture:** Review [COG_ARCHITECTURE.md](./COG_ARCHITECTURE.md) for data flow
3. **Deep dive:** Read [COG_RESPONSIBILITIES.md](./COG_RESPONSIBILITIES.md) for detailed boundaries

### For Adding New Features

**Decision Tree:**

```
Is it a slash command?
  ├─ YES → Which cog? (See COG_RESPONSIBILITIES.md)
  └─ NO → Is it a UI component?
      ├─ YES → Persistent or non-persistent? (See QUICK_REFERENCE.md)
      └─ NO → Is it business logic?
          ├─ YES → Add to Service Layer
          └─ NO → Add to Utils
```

---

## 📖 Key Concepts

### 1. Single Responsibility Principle

Each cog has **one clear responsibility**:

- ✅ **AdminCommands**: System operations only
- ✅ **NewsCommands**: News delivery only
- ✅ **SubscriptionCommands**: Subscription management only
- ❌ **NOT**: One cog doing multiple unrelated things

### 2. Separation of Concerns

- **Commands** orchestrate, don't implement
- **UI Components** handle interactions, don't contain business logic
- **Services** contain business logic, are stateless and reusable

### 3. Persistent vs Non-Persistent Components

| Feature              | Non-Persistent (InteractionsCog) | Persistent (PersistentViews) |
| -------------------- | -------------------------------- | ---------------------------- |
| Survives bot restart | ❌ No                            | ✅ Yes                       |
| Timeout              | ✅ Yes (default 180s)            | ❌ No (`timeout=None`)       |
| Use case             | Command responses                | Long-lived messages, DMs     |
| State reconstruction | ❌ Not needed                    | ✅ From `custom_id`          |

---

## 🔍 Common Tasks

### Add a New Slash Command

1. Identify the appropriate cog (see [COG_RESPONSIBILITIES.md](./COG_RESPONSIBILITIES.md))
2. Follow the pattern in [QUICK_REFERENCE.md](./QUICK_REFERENCE.md#pattern-1-add-a-new-slash-command)
3. Delegate business logic to service layer
4. Handle errors gracefully

### Add a New Button

1. Decide: Persistent or non-persistent?
2. Follow the pattern in [QUICK_REFERENCE.md](./QUICK_REFERENCE.md#pattern-2-add-a-new-interactive-button)
3. Implement callback with proper error handling
4. Register in appropriate cog

### Modify Existing Functionality

1. Find the responsible cog (see [COG_RESPONSIBILITIES.md](./COG_RESPONSIBILITIES.md))
2. Check if change belongs in cog or service layer
3. Update tests
4. Verify error handling

---

## 🐛 Debugging

### Command not showing in Discord?

1. Check if cog is loaded in `client.py`
2. Verify command is synced (`await self.tree.sync()`)
3. Check for decorator (`@app_commands.command()`)

### Button not responding?

1. Check if view is added to message
2. Verify `custom_id` is unique
3. Check logs for exceptions
4. Verify callback method signature

### Persistent button not working after restart?

1. Check if view is registered in `setup_hook()` with `timeout=None`
2. Verify `custom_id` parsing logic
3. Check logs for parsing errors

**More debugging tips:** [QUICK_REFERENCE.md](./QUICK_REFERENCE.md#quick-debugging-tips)

---

## 📊 Identified Issues & Recommendations

### High Priority

1. **Consolidate User Registration**
   - ❌ Current: Duplicated in `news_commands.py`
   - ✅ Fix: Use `@ensure_user_registered` decorator consistently

2. **Document Component Selection**
   - ❌ Current: No clear guidelines on persistent vs non-persistent
   - ✅ Fix: See [QUICK_REFERENCE.md](./QUICK_REFERENCE.md#component-selection-guide)

### Medium Priority

3. **Standardize Error Handling**
   - ⚠️ Current: Inconsistent error messages
   - ✅ Fix: Create shared error response builders

4. **Service Access Pattern**
   - ⚠️ Current: New service instances in every method
   - ✅ Fix: Consider dependency injection or singleton pattern

**Full analysis:** [COG_RESPONSIBILITIES.md](./COG_RESPONSIBILITIES.md#overlapping-functionality-analysis)

---

## 🧪 Testing

### Test Scope by Cog

- **AdminCommands**: Mock scheduler, test responses
- **NewsCommands**: Mock SupabaseService, test filtering
- **InteractionsCog**: Test callbacks, view composition
- **PersistentViews**: Test custom_id parsing, state reconstruction
- **ReadingListCog**: Test pagination, recommendations
- **SubscriptionCommands**: Test validation, subscription logic
- **NotificationSettings**: Test preference updates

**Full testing strategy:** [COG_ARCHITECTURE.md](./COG_ARCHITECTURE.md#testing-strategy-by-layer)

---

## 📝 Best Practices

### DO ✅

- Defer long operations (`await interaction.response.defer()`)
- Use specific exception types (`SupabaseServiceError`, `LLMServiceError`)
- Log with context (user_id, action, error_type)
- Handle message edit failures gracefully
- Delegate business logic to service layer

### DON'T ❌

- Implement business logic in cogs
- Create service instances in loops
- Ignore service exceptions
- Mix UI logic with business logic
- Forget to sync commands after changes

**Full list:** [QUICK_REFERENCE.md](./QUICK_REFERENCE.md#service-layer-guidelines)

---

## 🔗 Related Documentation

- **Service Layer:** `backend/app/services/README.md`
- **Error Handling:** `backend/app/core/ERROR_HANDLING_GUIDE.md`
- **Logger Usage:** `backend/app/core/LOGGER_USAGE.md`
- **Repository Pattern:** `backend/app/repositories/README.md`

---

## 📞 Need Help?

1. Check [QUICK_REFERENCE.md](./QUICK_REFERENCE.md) first
2. Review [COG_RESPONSIBILITIES.md](./COG_RESPONSIBILITIES.md) for boundaries
3. Study [COG_ARCHITECTURE.md](./COG_ARCHITECTURE.md) for data flow
4. Review existing cog implementations
5. Ask the team!

---

## 📅 Document History

- **Created:** 2024 (Task 13.1)
- **Purpose:** Define clear responsibilities for bot cogs
- **Requirements:** 7.1, 7.5
- **Status:** ✅ Complete

---

## 🎯 Summary

This documentation establishes:

1. ✅ **Clear single responsibilities** for each of the 7 cogs
2. ✅ **Identified overlapping functionality** (user registration, button definitions)
3. ✅ **Documented responsibility boundaries** (command, UI, service layers)
4. ✅ **Provided decision trees** for adding new features
5. ✅ **Created quick reference** for common tasks

**Result:** Improved maintainability, reduced confusion, clearer development guidelines.
