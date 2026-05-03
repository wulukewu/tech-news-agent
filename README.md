# Tech News Agent

An automated technical information curation system combining FastAPI backend, Next.js web interface, Discord Bot, and Groq LLM. It automatically fetches RSS feeds, analyzes articles with AI, and delivers personalized tech news through both a web dashboard and Discord DMs — with a full conversational AI layer, intelligent reminders, learning paths, and weekly insights.

## 🌟 Core Features

### 📱 Multi-Platform Access

- **Web Dashboard**: Modern Next.js interface with dark mode, i18n (EN/ZH), and full responsive design
- **Discord Bot**: Slash commands, DM notifications, and interactive UI components
- **REST API**: Full-featured API with Swagger/ReDoc documentation

### 🤖 AI-Powered Intelligence

- **Smart Scoring**: Evaluates technical depth using Groq (Llama 3.1 8B)
- **AI Summaries**: Generates concise summaries with Llama 3.3 70B
- **Personalized Recommendations**: Learns from your ratings to suggest relevant content
- **Deep Dive Analysis**: On-demand detailed technical breakdowns
- **QA Agent**: Full conversational Q&A over your subscribed articles with vector search, multi-turn memory, and user profile learning
- **Weekly Insights**: AI-generated weekly digest with trend detection and theme clustering
- **Intelligent Reminders**: Context-aware reminders based on reading behavior and interests
- **Learning Paths**: Skill tree, goal tracking, and adaptive content recommendations

### 👥 Multi-Tenant Architecture

- **Personal Subscriptions**: Each user manages their own RSS feeds
- **Private Reading Lists**: Rate and organize articles independently
- **Custom Notifications**: Granular control over frequency, timing, quiet hours, and content type thresholds
- **Data Isolation**: Complete privacy between users

### ⚡ Flexible Scheduling

- **Automated Fetching**: Configurable background scheduler (default: every 6 hours)
- **Per-User Dynamic Scheduling**: Each user's notifications follow their own schedule and timezone
- **Manual Triggers**: Instant article refresh via web, Discord, or API
- **Smart Notifications**: DM delivery with duplicate prevention and quiet hours support

### 🗄️ Robust Data Layer

- **Supabase/PostgreSQL**: Reliable data storage with pgvector support
- **Semantic Search**: Vector embeddings for AI-powered article search
- **Conversation Persistence**: Full chat history with search and export
- **Knowledge Graph**: Article dependency and concept linking

---

## 🚀 Quick Start

### Prerequisites

1. **Supabase Account** — [supabase.com](https://supabase.com)
2. **Discord Bot** (optional) — [Discord Developer Portal](https://discord.com/developers/applications)
3. **Groq API Key** — [console.groq.com](https://console.groq.com)

### Installation

#### Option 1: Docker Compose (Recommended)

```bash
# 1. Clone the repository
git clone https://github.com/yourusername/tech-news-agent.git
cd tech-news-agent

# 2. Set up environment variables
cp .env.example .env
# Edit .env with your credentials

# 3. Initialize database
# Run backend/scripts/init_supabase.sql in Supabase SQL Editor

# 4. Start services
docker compose up -d

# 5. Access the application
# Web:      http://localhost:3000
# API:      http://localhost:8000
# API Docs: http://localhost:8000/docs
```

#### Option 2: Local Development

```bash
# Backend
cd backend
pip install -r requirements.txt
python -m app.main

# Frontend (in another terminal)
cd frontend
npm install
npm run dev
```

### First Steps

1. **Web Interface**: Visit http://localhost:3000 and sign in with Discord OAuth
2. **Subscribe to Feeds**: Add your favorite RSS feeds from the Subscriptions page
3. **Trigger Fetch**: Click "Fetch New Articles" or use `/trigger_fetch` in Discord
4. **Explore**: Browse articles, save to reading list, rate content, and chat with the AI

---

## How to Run

### Method 1: Docker Compose (Recommended)

#### 🔧 Development (with Hot Reloading)

```bash
make dev
# or
docker-compose up -d
```

#### 🚀 Production

```bash
make prod
# or
docker-compose -f docker-compose.prod.yml up -d
```

### Method 2: Local Python

```bash
pip install -r requirements.txt
python -m app.main
```

---

## ⚙️ Environment Variables

### Required

```bash
# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-service-role-key

# Groq AI
GROQ_API_KEY=your-groq-api-key

# JWT Authentication
JWT_SECRET_KEY=your-secret-key-here   # openssl rand -hex 32
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30

# Discord OAuth (for web login)
DISCORD_CLIENT_ID=your-client-id
DISCORD_CLIENT_SECRET=your-client-secret
DISCORD_REDIRECT_URI=http://localhost:3000/auth/callback

# Frontend
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### Optional

```bash
# Discord Bot
DISCORD_TOKEN=your-bot-token
DISCORD_CHANNEL_ID=your-channel-id

# Scheduler
SCHEDULER_CRON=0 */6 * * *
SCHEDULER_TIMEZONE=Asia/Taipei

# Application
TIMEZONE=Asia/Taipei
RSS_FETCH_DAYS=7
BATCH_SIZE=50
LOG_LEVEL=INFO
```

---

## 💬 Discord Bot Commands

### Scheduler

| Command | Description |
|---------|-------------|
| `/trigger_fetch` | Manually trigger article fetching |
| `/scheduler_status` | Check scheduler health and status |

### Feed Management

| Command | Description |
|---------|-------------|
| `/add_feed name: url: category:` | Subscribe to an RSS/Atom feed |
| `/list_feeds` | View all subscribed feeds |
| `/unsubscribe_feed feed_identifier:` | Unsubscribe from a feed |

### Article Discovery

| Command | Description |
|---------|-------------|
| `/news_now` | Latest articles with category filter, deep dive, and save buttons |
| `/ask question:` | Ask a natural language question about your articles |

### Reading List

| Command | Description |
|---------|-------------|
| `/reading_list view` | Browse with pagination, mark read, and rate (1–5 stars) |
| `/reading_list remove article_id:` | Remove an article by ID |
| `/reading_list recommend` | AI recommendations based on 4+ star ratings |

### Conversations

| Command | Description |
|---------|-------------|
| `/conversations` | List past DM conversations |
| `/continue id:` | Continue a past conversation |
| `/search query:` | Search conversation history |

### Profile & Recommendations

| Command | Description |
|---------|-------------|
| `/my_profile` | View preference summary and category weights |
| `/update_profile` | Rebuild preference summary from DM history |
| `/recommend_now` | Trigger personalized recommendation to DM |
| `/stats` | Reading statistics: saved, read/unread, avg rating, top categories |
| `/export` | Export reading list as CSV |

### Notification Settings

| Command | Description |
|---------|-------------|
| `/notifications enabled:` | Toggle DM notifications on/off |
| `/notification_status` | Check current notification settings |
| `/set-notification-frequency frequency:` | Set daily/weekly frequency |
| `/set-notification-time hour: minute:` | Set delivery time |
| `/set-timezone timezone:` | Set your timezone |
| `/toggle-notifications` | Quick toggle |
| `/quiet-hours` | View quiet hours settings |
| `/set-quiet-hours start_time: end_time: enabled:` | Configure quiet hours |
| `/toggle-quiet-hours` | Quick toggle quiet hours |

---

## 🌐 Web API Endpoints

### Authentication
```
POST /api/auth/discord/login
POST /api/auth/discord/callback
GET  /api/auth/me
```

### Articles
```
GET  /api/articles
GET  /api/articles/{id}
POST /api/articles/{id}/analyze
```

### Feeds
```
GET    /api/feeds
POST   /api/feeds
GET    /api/feeds/subscriptions
POST   /api/feeds/subscribe
DELETE /api/feeds/unsubscribe
```

### Reading List
```
GET    /api/reading-list
POST   /api/reading-list
PATCH  /api/reading-list/{id}
DELETE /api/reading-list/{id}
GET    /api/reading-list/recommend
```

### QA / Conversations
```
POST /api/qa/ask
GET  /api/conversations
GET  /api/conversations/{id}
GET  /api/conversations/{id}/messages
POST /api/conversations/{id}/ai
GET  /api/conversations/{id}/insights
GET  /api/conversations/{id}/related
POST /api/conversations/{id}/share
GET  /api/conversations/{id}/export
```

### Notifications
```
GET  /api/notifications/preferences
PUT  /api/notifications/preferences
GET  /api/notifications/quiet-hours
PUT  /api/notifications/quiet-hours
GET  /api/notifications/history
GET  /api/notifications/settings
PUT  /api/notifications/settings
POST /api/notifications/proactive
```

### Learning
```
GET  /api/learning/goals
POST /api/learning/goals
GET  /api/learning/progress
GET  /api/learning/evaluation
GET  /api/learning-content
GET  /api/weekly-insights
POST /api/intelligent-reminder
GET  /api/reminder-settings
PUT  /api/reminder-settings
```

### Analytics & System
```
GET  /api/analytics
GET  /api/knowledge-graph
GET  /api/user/platforms
POST /api/scheduler/trigger
GET  /api/scheduler/status
GET  /health
GET  /health/scheduler
```

Full interactive docs at `/docs` (Swagger) or `/redoc` when running the backend.

---

## 🧪 Testing

```bash
# Before pushing — run CI checks locally
./scripts/ci-fix.sh          # Auto-fix formatting/linting
./scripts/ci-local-test.sh   # Full CI check (mirrors GitHub Actions)
```

### Backend

```bash
cd backend
pytest -v
pytest --cov=app --cov-report=html

# Hypothesis profiles
HYPOTHESIS_PROFILE=dev pytest tests/test_database_properties.py -v   # fast (10 examples)
HYPOTHESIS_PROFILE=ci  pytest tests/test_database_properties.py -v   # CI  (100 examples)
```

### Frontend

```bash
cd frontend
npm test                 # unit tests
npm run test:coverage    # with coverage
npm run test:e2e         # Playwright E2E
```

---

## 📁 Project Structure

```
tech-news-agent/
├── backend/
│   ├── app/
│   │   ├── api/               # REST API endpoints
│   │   │   ├── auth.py
│   │   │   ├── articles.py
│   │   │   ├── feeds.py
│   │   │   ├── reading_list.py
│   │   │   ├── scheduler.py
│   │   │   ├── qa.py
│   │   │   ├── conversations/  # conversation CRUD, messages, AI, insights, share, export
│   │   │   ├── notifications/  # preferences, quiet_hours, history, settings, proactive
│   │   │   ├── learning_path/  # goals, progress, evaluation
│   │   │   ├── weekly_insights.py
│   │   │   ├── intelligent_reminder.py
│   │   │   ├── knowledge_graph.py
│   │   │   ├── analytics.py
│   │   │   └── ...
│   │   ├── bot/
│   │   │   ├── cogs/
│   │   │   │   ├── news_commands.py
│   │   │   │   ├── reading_list.py
│   │   │   │   ├── subscription_commands.py
│   │   │   │   ├── notification_settings.py
│   │   │   │   ├── quiet_hours_settings.py
│   │   │   │   ├── conversation_commands.py
│   │   │   │   ├── qa_commands.py
│   │   │   │   ├── proactive_dm.py
│   │   │   │   ├── dm_conversation_listener.py
│   │   │   │   ├── conversation_auto_manager.py
│   │   │   │   ├── persistent_views.py
│   │   │   │   ├── interactions.py
│   │   │   │   └── admin_commands.py
│   │   │   └── client.py
│   │   ├── services/          # ~50 service files (mixin pattern)
│   │   │   ├── supabase_service.py
│   │   │   ├── llm_service.py
│   │   │   ├── rss_service.py
│   │   │   ├── dynamic_scheduler.py
│   │   │   ├── smart_conversation.py
│   │   │   ├── enhanced_recommendation_engine.py
│   │   │   ├── intelligent_reminder_generator.py
│   │   │   ├── cross_platform_sync.py
│   │   │   └── _mixins/       # article, feed, reading_list, notification, user
│   │   ├── qa_agent/          # Full QA subsystem
│   │   │   ├── qa_agent_controller.py
│   │   │   ├── query_processor.py
│   │   │   ├── retrieval_engine.py
│   │   │   ├── response_generator.py
│   │   │   ├── conversation_manager.py
│   │   │   ├── user_profile_manager.py
│   │   │   ├── knowledge_graph/
│   │   │   ├── intelligent_reminder/
│   │   │   ├── weekly_insights/
│   │   │   ├── proactive_learning/
│   │   │   └── learning_path/
│   │   ├── core/              # config, exceptions, logger, validators
│   │   ├── repositories/      # data access layer
│   │   ├── schemas/           # Pydantic models
│   │   └── tasks/             # APScheduler jobs
│   ├── scripts/               # DB scripts, migrations, utilities
│   ├── tests/                 # pytest test suite
│   └── requirements.txt
│
├── frontend/
│   ├── app/
│   │   ├── (public)/          # /, /login, /auth/callback, /chat, /conversations, /demo
│   │   └── app/               # authenticated routes
│   │       ├── articles/
│   │       ├── reading-list/
│   │       ├── subscriptions/
│   │       ├── recommendations/
│   │       ├── chat/
│   │       ├── learning/
│   │       ├── insights/
│   │       ├── knowledge-graph/
│   │       ├── reminders/
│   │       ├── analytics/
│   │       └── settings/      # notifications, reminders, preferences, appearance, account
│   ├── features/              # feature-sliced components
│   │   ├── articles/
│   │   ├── ai-analysis/
│   │   ├── notifications/
│   │   ├── recommendations/
│   │   ├── subscriptions/
│   │   └── system-monitor/
│   ├── components/            # shared UI components (shadcn/ui)
│   ├── lib/                   # API client, hooks, utils
│   ├── locales/               # i18n (EN/ZH)
│   └── package.json
│
├── docs/                      # All documentation
├── scripts/                   # Dev, CI, migration scripts
├── .github/workflows/ci.yml
├── docker-compose.yml         # Development
├── docker-compose.prod.yml    # Production
├── Makefile
└── README.md
```

---

## 🏗️ Architecture

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

### Tech Stack

**Frontend**: Next.js 14 (App Router), React 18, TypeScript, Tailwind CSS, shadcn/ui, React Query, next-intl, Playwright

**Backend**: Python 3.11+, FastAPI, discord.py 2.4+, APScheduler 3.10+, Supabase Python client

**Infrastructure**: Supabase (PostgreSQL + pgvector), Docker + Docker Compose, Groq Cloud (Llama 3.1 8B / 3.3 70B)

---

## 📊 Database Schema

```
users                    feeds                   articles
├── id (UUID)           ├── id (UUID)           ├── id (UUID)
├── discord_id          ├── name                ├── feed_id (FK)
├── dm_notifications    ├── url                 ├── title
└── created_at          ├── category            ├── url
                        └── is_active           ├── published_at
user_subscriptions                              ├── tinkering_index
├── user_id (FK)        reading_list            ├── ai_summary
└── feed_id (FK)        ├── user_id (FK)        ├── embedding (vector)
                        ├── article_id (FK)     └── created_at
conversations           ├── status
├── id (UUID)           └── rating              user_notification_preferences
├── user_id (FK)                                ├── user_id (FK)
├── title               messages                ├── frequency
└── created_at          ├── conversation_id     ├── notification_time
                        ├── role                ├── timezone
knowledge_graph         └── content             └── quiet_hours_*
├── article_id (FK)
├── concept
└── relationships
```

---

## 🔧 Troubleshooting

**Database errors / missing tables:**
```bash
cd backend
python3 scripts/verify_bot_health.py
python3 scripts/apply_missing_migration.py
```

**Discord bot not responding:** Check `DISCORD_TOKEN`, bot permissions, and OAuth scopes.

**Articles not fetching:** Check scheduler logs (`docker-compose logs -f backend`), verify RSS feeds are valid, and confirm Groq API key has credits.

For more, see [docs/troubleshooting/](./docs/troubleshooting/).

---

## 📚 Documentation

- [Quick Start Guide](./docs/guides/quick-start.md)
- [Environment Setup](./docs/setup/env-setup-guide.md)
- [Docker Guide](./docs/docker/docker-guide.md)
- [User Guide](./docs/guides/user-guide.md)
- [Developer Guide](./docs/development/developer-guide.md)
- [Architecture Overview](./docs/architecture/architecture-overview.md)
- [Deployment Guide](./docs/deployment/deployment-guide.md)
- [Complete Docs Index](./docs/README.md)

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Make changes and add tests
4. Run checks: `./scripts/ci-fix.sh && ./scripts/ci-local-test.sh`
5. Commit: `git commit -m 'feat(scope): add amazing feature'`
6. Push and open a Pull Request

---

## 📝 License

MIT License — see [LICENSE](LICENSE) for details.

## 🙏 Acknowledgments

[Supabase](https://supabase.com) · [Groq](https://groq.com) · [Discord](https://discord.com) · [Vercel/Next.js](https://nextjs.org) · [shadcn/ui](https://ui.shadcn.com)
