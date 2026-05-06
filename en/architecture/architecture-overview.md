# Architecture Overview

> Last Updated: 2026-05-04

---

## High-Level Overview

Tech News Agent is a multi-platform, AI-powered news curation system. It combines a FastAPI backend, Next.js web dashboard, and Discord Bot — all backed by Supabase (PostgreSQL + pgvector) and Groq LLM.

```
┌─────────────────┐     ┌──────────────────────┐     ┌─────────────────┐
│   Next.js Web   │────▶│   FastAPI Backend     │────▶│    Supabase     │
│   Dashboard     │     │   + Discord Bot       │     │   PostgreSQL    │
│   (i18n EN/ZH)  │     │   + QA Agent          │     │   + pgvector    │
└─────────────────┘     └──────────────────────┘     └─────────────────┘
        │                         │                           │
        ▼                         ▼                           ▼
  Discord OAuth            Groq LLM API              Vector Search
  React Query              APScheduler               Conversation Store
  Feature Slices           Dynamic Scheduler         Knowledge Graph
```

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **Frontend** | Next.js 14 (App Router), React 18, TypeScript, Tailwind CSS, shadcn/ui |
| **State / Data Fetching** | React Query, Split Context pattern |
| **i18n** | next-intl (EN / ZH) |
| **Backend** | FastAPI, Python 3.11+ |
| **Discord Bot** | discord.py 2.4+ |
| **Scheduler** | APScheduler 3.10+ |
| **Database** | Supabase (PostgreSQL + pgvector) |
| **AI / LLM** | Groq Cloud — Llama 3.1 8B (scoring), Llama 3.3 70B (summaries) |
| **Auth** | Discord OAuth (web login), JWT |
| **Testing** | pytest, Hypothesis, Jest, Playwright |

---

## Core Architecture Patterns

### 1. Repository Pattern (`app/repositories/`)

Abstracts all database access behind typed interfaces. Each entity (users, articles, feeds, reading list, etc.) has a dedicated repository. Repositories handle CRUD, soft delete, audit trails, and business rule validation — keeping SQL out of the service layer.

### 2. Service Layer with Mixin Pattern (`app/services/`)

~50 service files implement business logic. Large service classes are composed from focused mixins located in `app/services/_mixins/` (article, feed, reading_list, notification, user). This keeps individual files small while allowing rich service objects.

```
SupabaseService
  ├── ArticleMixin       (fetch, score, summarize)
  ├── FeedMixin          (subscribe, unsubscribe, validate)
  ├── ReadingListMixin   (save, rate, recommend)
  ├── NotificationMixin  (send DM, quiet hours, history)
  └── UserMixin          (profile, preferences, stats)
```

### 3. QA Agent Subsystem (`app/qa_agent/`)

A self-contained subsystem that provides conversational AI over a user's subscribed articles. Components:

| Component | Responsibility |
|-----------|---------------|
| `qa_agent_controller.py` | Entry point; orchestrates the full QA pipeline |
| `query_processor.py` | Parses and classifies incoming questions |
| `retrieval_engine.py` | Vector search via pgvector embeddings |
| `response_generator.py` | Calls Groq LLM to produce answers |
| `conversation_manager.py` | Persists multi-turn chat history |
| `user_profile_manager.py` | Learns preferences from ratings and history |
| `security_manager.py` | Enforces per-user data isolation |
| `performance_monitor.py` | Tracks latency and token usage |

Sub-modules extend the QA agent with higher-level features:

- `knowledge_graph/` — article dependency and concept linking
- `intelligent_reminder/` — context-aware reading reminders
- `weekly_insights/` — trend detection and theme clustering
- `proactive_learning/` — adaptive content recommendations
- `learning_path/` — skill tree and goal tracking

### 4. Feature-Sliced Frontend (`frontend/features/`)

Frontend code is organized by feature domain rather than by file type:

```
frontend/features/
├── articles/
├── ai-analysis/
├── notifications/
├── recommendations/
├── subscriptions/
└── system-monitor/
```

Each feature slice owns its components, hooks, and API calls. Shared UI primitives live in `frontend/components/` (shadcn/ui).

### 5. Split Context Pattern (`frontend/contexts/`)

React contexts are split by concern (Auth, User, Theme) to minimize re-render scope. Server state (articles, feeds, reading list) is managed by React Query with configurable stale/cache times.

### 6. Centralized Error Handling & Logging (`app/core/`)

- `app/core/exceptions.py` — typed `AppException` hierarchy with `ErrorCode` enum
- `app/core/logger.py` — structured JSON logging with request-scoped context (request ID, user ID) via `contextvars`
- FastAPI exception handlers map `AppException` to consistent JSON error responses

---

## Data Flow

### API Request Flow

```
Browser / Discord Bot
  → FastAPI route
  → Auth middleware (JWT validation)
  → Service layer (business logic, mixin composition)
  → Repository layer (Supabase query)
  → Standardized JSON response
```

### Notification Flow

```
APScheduler (per-user dynamic schedule)
  → dynamic_scheduler.py evaluates each user's timezone, frequency, quiet hours
  → NotificationMixin fetches relevant articles
  → LLM generates personalized summary (Llama 3.3 70B)
  → discord.py sends DM
  → Notification history recorded in Supabase
```

### QA / Conversation Flow

```
User question (web or Discord)
  → qa_agent_controller
  → query_processor (classify intent)
  → retrieval_engine (pgvector similarity search)
  → response_generator (Groq LLM with retrieved context)
  → conversation_manager (persist turn to Supabase)
  → Response returned to user
```

---

## Multi-Tenant Design

Every user-facing resource is scoped by `user_id`:

- **Subscriptions** — each user manages their own RSS feed list (`user_subscriptions` table)
- **Reading list** — private per user; ratings feed the recommendation engine
- **Notification preferences** — per-user frequency, delivery time, timezone, quiet hours
- **Conversations** — chat history is isolated per user; `security_manager.py` enforces this at the QA layer
- **Dynamic scheduler** — `dynamic_scheduler.py` maintains a per-user job in APScheduler, respecting each user's schedule and timezone

There is no shared global feed or reading list. Data isolation is enforced at both the repository layer (all queries filter by `user_id`) and the QA agent's `security_manager`.

---

## Key Design Decisions

**Mixin-based service composition over inheritance chains** — With ~50 service concerns, deep inheritance becomes unmanageable. Mixins allow `SupabaseService` to compose only the capabilities it needs while keeping each mixin independently testable.

**pgvector for semantic search** — Storing article embeddings directly in Supabase (PostgreSQL) avoids a separate vector database. This simplifies the infrastructure while supporting similarity search for the QA retrieval engine and recommendations.

**QA Agent as a self-contained subsystem** — Isolating the conversational AI into `app/qa_agent/` with its own controller, retrieval, and profile management means it can evolve independently of the core CRUD API without coupling concerns.

**Dynamic per-user scheduler** — A single global cron would send notifications at the wrong time for users in different timezones. `dynamic_scheduler.py` registers individual APScheduler jobs per user, each with its own schedule derived from the user's preferences.

**Feature-sliced frontend** — Grouping by feature (not by `components/`, `hooks/`, `utils/`) means all code for a feature is co-located, reducing the cognitive overhead of cross-cutting changes.

**Discord OAuth as the sole identity provider** — Since the Discord Bot is a first-class client, using Discord OAuth for web login means there is one user identity across both surfaces, simplifying the user model and eliminating a separate registration flow.
