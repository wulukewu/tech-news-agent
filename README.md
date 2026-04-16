# Tech News Agent

An automated technical information curation system combining FastAPI backend, Next.js web interface, Discord Bot, and Groq LLM. It automatically fetches RSS feeds, analyzes articles with AI, and delivers personalized tech news through both web dashboard and Discord DMs.

## 🌟 Core Features

### 📱 Multi-Platform Access

- **Web Dashboard**: Modern Next.js interface with dark mode support
- **Discord Bot**: Interactive commands and DM notifications
- **REST API**: Full-featured API for programmatic access

### 🤖 AI-Powered Intelligence

- **Smart Scoring**: Evaluates technical depth using Groq (Llama 3.1 8B)
- **AI Summaries**: Generates concise summaries with Llama 3.3 70B
- **Personalized Recommendations**: Learns from your ratings to suggest relevant content
- **Deep Dive Analysis**: On-demand detailed technical breakdowns

### 👥 Multi-Tenant Architecture

- **Personal Subscriptions**: Each user manages their own RSS feeds
- **Private Reading Lists**: Rate and organize articles independently
- **Custom Notifications**: Control when and how you receive updates
- **Data Isolation**: Complete privacy between users

### ⚡ Flexible Scheduling

- **Automated Fetching**: Configurable background scheduler (default: every 6 hours)
- **Manual Triggers**: Instant article refresh via web, Discord, or API
- **Smart Notifications**: DM delivery 10 minutes after article processing

### 🗄️ Robust Data Layer

- **Supabase/PostgreSQL**: Reliable data storage with pgvector support
- **Semantic Search Ready**: Vector embeddings for future AI-powered search
- **Efficient Indexing**: Optimized queries with proper database indexes

---

## 🚀 Quick Start

> **⚡ 快速設定**: 查看 [環境變數快速設定指南](./QUICK_ENV_SETUP.md) 5 分鐘完成配置

### Prerequisites

1. **Supabase Account** - [Sign up at supabase.com](https://supabase.com)
2. **Discord Bot** (optional) - [Create at Discord Developer Portal](https://discord.com/developers/applications)
3. **Groq API Key** - [Get from Groq Cloud](https://console.groq.com)

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
# Web: http://localhost:3000
# API: http://localhost:8000
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
2. **Subscribe to Feeds**: Add your favorite RSS feeds from the dashboard
3. **Trigger Fetch**: Click "Fetch New Articles" to get your first batch
4. **Explore**: Browse articles, save to reading list, and rate content

For detailed setup instructions, see [Quick Start Guide](./docs/QUICKSTART.md).

---

## How to Run

### Method 1: Using Docker Compose (Recommended)

#### 🔧 Development Environment (with Hot Reloading)

```bash
# Quick start
make dev

# Or using docker-compose directly
docker-compose up -d

# View logs
make logs-dev
```

#### 🚀 Production Environment

```bash
# Quick start
make prod

# Or using docker-compose directly
docker-compose -f docker-compose.prod.yml up -d

# View logs
make logs-prod
```

**📚 詳細說明:**

- [環境變數設定指南](./docs/setup/ENV_SETUP_GUIDE.md) - 環境變數完整說明
- [快速開始指南](./docs/QUICKSTART.md) - 快速上手
- [Docker 完整指南](./docs/docker/DOCKER_GUIDE.md) - 詳細文件

### Method 2: Local Python Execution

1. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

2. Configure environment variables (create `.env`).

3. Start the application:
   ```bash
   python -m app.main
   ```

---

## ⚙️ Environment Variables

### Required Variables

```bash
# Supabase Configuration
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-service-role-key

# Groq AI Configuration
GROQ_API_KEY=your-groq-api-key

# JWT Authentication (generate with: openssl rand -hex 32)
JWT_SECRET_KEY=your-secret-key-here
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30

# Discord OAuth (for web login)
DISCORD_CLIENT_ID=your-client-id
DISCORD_CLIENT_SECRET=your-client-secret
DISCORD_REDIRECT_URI=http://localhost:3000/auth/callback

# Frontend Configuration
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### Optional Variables

```bash
# Discord Bot (optional - for Discord integration)
DISCORD_TOKEN=your-bot-token
DISCORD_CHANNEL_ID=your-channel-id  # For channel notifications

# Scheduler Configuration
SCHEDULER_CRON=0 */6 * * *          # Every 6 hours
DM_NOTIFICATION_CRON=10 */6 * * *   # 10 minutes after fetch
SCHEDULER_TIMEZONE=Asia/Taipei

# Application Settings
TIMEZONE=Asia/Taipei
RSS_FETCH_DAYS=7                    # Fetch articles from last N days
BATCH_SIZE=50                       # Articles per batch
BATCH_SPLIT_THRESHOLD=100           # When to split batches

# Development
LOG_LEVEL=INFO                      # DEBUG, INFO, WARNING, ERROR
```

For detailed configuration guide, see [Environment Setup Guide](./docs/setup/ENV_SETUP_GUIDE.md).

---

## 💬 Discord Bot Commands

### Scheduler Management

#### `/trigger_fetch`

Manually trigger article fetching immediately.

```
/trigger_fetch
```

#### `/scheduler_status`

Check scheduler execution status and health.

```
/scheduler_status
```

### Feed Management

#### `/add_feed`

Subscribe to an RSS/Atom feed.

```
/add_feed name:Hacker News url:https://news.ycombinator.com/rss category:Tech News
```

#### `/list_feeds`

View all your subscribed feeds.

```
/list_feeds
```

#### `/unsubscribe_feed`

Unsubscribe from a feed.

```
/unsubscribe_feed feed_name:Hacker News
```

### Article Discovery

#### `/news_now`

View latest articles from your subscribed feeds with interactive filters and deep-dive analysis.

```
/news_now
```

**Features:**

- 📋 Category filter dropdown
- 📖 Deep dive analysis buttons (up to 5 articles)
- ⭐ Read later buttons (up to 10 articles)

### Reading List

#### `/reading_list view`

Browse your reading list with pagination.

```
/reading_list view
```

**Features:**

- 5 articles per page
- ✅ Mark as read buttons
- ⭐ Rating dropdowns (1-5 stars)
- Previous/Next navigation

#### `/reading_list recommend`

Get AI-generated recommendations based on your highly-rated articles (4+ stars).

```
/reading_list recommend
```

### Notification Settings

#### `/notifications`

Toggle DM notifications on/off.

```
/notifications enabled:開啟通知
/notifications enabled:關閉通知
```

#### `/notification_status`

Check your current notification settings.

```
/notification_status
```

For complete command documentation, see [User Guide](./docs/USER_GUIDE.md).

## 🌐 Web API Endpoints

### Authentication

```http
POST /api/auth/discord/login
POST /api/auth/discord/callback
GET  /api/auth/me
```

### Articles

```http
GET  /api/articles              # List articles
GET  /api/articles/{id}         # Get article details
POST /api/articles/{id}/analyze # Deep dive analysis
```

### Feeds

```http
GET    /api/feeds               # List all feeds
POST   /api/feeds               # Create feed
GET    /api/feeds/subscriptions # User's subscriptions
POST   /api/feeds/subscribe     # Subscribe to feed
DELETE /api/feeds/unsubscribe   # Unsubscribe from feed
```

### Reading List

```http
GET    /api/reading-list        # Get reading list
POST   /api/reading-list        # Add to reading list
PATCH  /api/reading-list/{id}   # Update status/rating
DELETE /api/reading-list/{id}   # Remove from list
GET    /api/reading-list/recommend # Get recommendations
```

### Scheduler

```http
POST /api/scheduler/trigger     # Trigger manual fetch
GET  /api/scheduler/status      # Get scheduler status
```

### Health Checks

```http
GET /                           # Basic health check
GET /health                     # Detailed health status
GET /health/scheduler           # Scheduler health
```

For complete API documentation, visit `/docs` (Swagger UI) or `/redoc` (ReDoc) when running the backend.

---

## Interactive UI Elements

All interactive elements persist across bot restarts, meaning buttons and menus continue to work even if the bot goes offline and comes back.

### Filter Select Menu

- **Location**: Appears with every `/news_now` notification
- **Function**: Filter articles by category in real-time
- **Options**: "📋 顯示全部" (Show All) + up to 24 most common categories
- **Response**: Ephemeral message (only you see it) with filtered results

### Deep Dive Buttons

- **Location**: Up to 5 buttons per `/news_now` notification
- **Label**: 📖 followed by article title (truncated to 20 chars)
- **Function**: Generates detailed technical analysis including:
  - Core technical concepts
  - Application scenarios
  - Potential risks
  - Recommended next steps
- **Model**: Uses Llama 3.3 70B for high-quality summaries
- **Response**: Ephemeral message with up to 600 tokens of analysis

### Rating Select Menus

- **Location**: In `/reading_list view` pagination interface
- **Options**: ⭐ (1 star) through ⭐⭐⭐⭐⭐ (5 stars)
- **Function**: Rate articles in your reading list
- **Use Case**: Build your reading preferences for personalized recommendations

---

## 🧪 Testing

### Backend Tests

```bash
cd backend

# Run all tests
pytest -v

# Run specific test suites
pytest tests/test_database_properties.py -v  # Property-based tests (17 properties)
pytest tests/test_config.py -v              # Configuration tests
pytest tests/test_sql_init_integration.py -v # SQL initialization tests

# Run with coverage
pytest --cov=app --cov-report=html

# Adjust Hypothesis test intensity
HYPOTHESIS_PROFILE=dev pytest tests/test_database_properties.py -v  # Fast (10 examples)
HYPOTHESIS_PROFILE=ci pytest tests/test_database_properties.py -v   # CI (100 examples)
```

### Frontend Tests

```bash
cd frontend

# Unit tests
npm test                    # Run once
npm run test:watch          # Watch mode
npm run test:coverage       # With coverage

# E2E tests
npm run test:e2e           # Headless
npm run test:e2e:ui        # Interactive UI
```

### Test Coverage

- **Backend**: 17 property-based tests + unit tests + integration tests
- **Frontend**: Jest unit tests + Playwright E2E tests
- **Database**: Comprehensive schema validation with Hypothesis

For detailed testing documentation, see [Testing Guide](./docs/testing/supabase-migration-testing.md).

## 📚 Documentation

### Getting Started

- **[Quick Start Guide](./docs/QUICKSTART.md)** - Get up and running in minutes
- **[Environment Setup](./docs/setup/ENV_SETUP_GUIDE.md)** - Complete environment variable reference
- **[Docker Guide](./docs/docker/DOCKER_GUIDE.md)** - Docker deployment instructions

### User Guides

- **[User Guide](./docs/USER_GUIDE.md)** - Using the web interface and Discord bot
- **[Manual Scheduler Trigger](./docs/MANUAL_SCHEDULER_TRIGGER.md)** - On-demand article fetching

### Developer Resources

- **[Developer Guide](./docs/DEVELOPER_GUIDE.md)** - Architecture and API reference
- **[Project Overview](./docs/PROJECT_OVERVIEW.md)** - Comprehensive system documentation
- **[Architecture](./docs/ARCHITECTURE.md)** - System architecture details
- **[Testing Guide](./docs/testing/supabase-migration-testing.md)** - Testing strategies and tools

### Deployment

- **[Deployment Guide](./docs/deployment/DEPLOYMENT.md)** - Production deployment steps
- **[Deployment Checklist](./docs/deployment/DEPLOYMENT_CHECKLIST.md)** - Pre-deployment verification
- **[Public Bot Setup](./docs/PUBLIC_BOT_SETUP.md)** - Making your bot public

📖 **[Complete Documentation Index](./docs/README.md)** - Browse all documentation

### Manual End-to-End Test

1. Fill in all environment variables in `.env`
2. Run the bot and trigger `/news_now` in Discord
3. Verify:
   - Discord receives a notification with stats and article list
   - Interactive buttons work:
     - Filter menu filters by category
     - Deep Dive buttons generate AI summaries
4. Test `/reading_list view`:
   - Verify pagination works (Previous/Next buttons)
   - Test Mark as Read buttons
   - Test rating dropdowns (1-5 stars)
5. Test `/reading_list recommend`:
   - Rate some articles 4-5 stars first
   - Verify AI-generated recommendations appear

---

## 📁 Project Structure

```
tech-news-agent/
├── backend/                    # FastAPI backend + Discord bot
│   ├── app/
│   │   ├── api/               # REST API endpoints
│   │   │   ├── auth.py        # Authentication routes
│   │   │   ├── articles.py    # Article management
│   │   │   ├── feeds.py       # Feed subscriptions
│   │   │   ├── reading_list.py # Reading list operations
│   │   │   └── scheduler.py   # Manual scheduler triggers
│   │   ├── bot/               # Discord bot
│   │   │   ├── cogs/          # Command groups
│   │   │   │   ├── admin_commands.py      # Admin utilities
│   │   │   ├── interactions.py    # Interactive UI components
│   │   │   │   ├── news_commands.py       # /news_now command
│   │   │   │   ├── reading_list.py        # Reading list commands
│   │   │   │   └── subscription_commands.py # Feed management
│   │   │   └── client.py      # Bot client setup
│   │   ├── core/              # Core configuration
│   │   │   ├── config.py      # Environment settings
│   │   │   └── exceptions.py  # Custom exceptions
│   │   ├── schemas/           # Pydantic models
│   │   │   └── article.py     # Data schemas
│   │   ├── services/          # Business logic
│   │   │   ├── llm_service.py      # Groq LLM integration
│   │   │   ├── supabase_service.py # Database operations
│   │   │   └── rss_service.py      # RSS fetching
│   │   ├── tasks/             # Background jobs
│   │   │   └── scheduler.py   # APScheduler tasks
│   │   └── main.py            # Application entry point
│   ├── scripts/               # Database scripts
│   │   ├── init_supabase.sql  # Schema initialization
│   │   └── seed_feeds.py      # Default feeds
│   ├── tests/                 # Backend tests
│   │   ├── test_database_properties.py  # Property tests
│   │   ├── test_config.py               # Config tests
│   │   └── ...
│   ├── Dockerfile             # Production image
│   ├── Dockerfile.dev         # Development image
│   └── requirements.txt       # Python dependencies
│
├── frontend/                  # Next.js web interface
│   ├── app/                   # App router pages
│   │   ├── (auth)/           # Auth pages
│   │   │   ├── login/        # Login page
│   │   │   └── auth/callback/ # OAuth callback
│   │   ├── dashboard/        # Main dashboard
│   │   ├── reading-list/     # Reading list page
│   │   └── layout.tsx        # Root layout
│   ├── components/           # React components
│   │   ├── ui/              # shadcn/ui components
│   │   ├── ArticleCard.tsx  # Article display
│   │   ├── FeedManager.tsx  # Feed management
│   │   └── ...
│   ├── lib/                 # Utilities
│   │   ├── api/            # API client
│   │   │   ├── articles.ts
│   │   │   ├── feeds.ts
│   │   │   └── scheduler.ts
│   │   └── utils.ts        # Helper functions
│   ├── hooks/              # Custom React hooks
│   ├── contexts/           # React contexts
│   ├── __tests__/          # Unit tests
│   ├── e2e/                # E2E tests
│   ├── Dockerfile          # Production image
│   ├── Dockerfile.dev      # Development image
│   └── package.json        # Node dependencies
│
├── docs/                   # Documentation
│   ├── setup/             # Setup guides
│   ├── docker/            # Docker documentation
│   ├── deployment/        # Deployment guides
│   ├── testing/           # Testing documentation
│   └── development/       # Development notes
│
├── .github/
│   └── workflows/
│       └── ci.yml         # GitHub Actions CI
│
├── docker-compose.yml     # Development compose
├── docker-compose.prod.yml # Production compose
├── .env.example           # Environment template
├── Makefile              # Development shortcuts
└── README.md             # This file
```

---

## 🎯 Key Features

### Web Dashboard

- **Modern UI**: Built with Next.js 14, React 18, and Tailwind CSS
- **Dark Mode**: Seamless theme switching with next-themes
- **Real-time Updates**: React Query for efficient data fetching
- **Responsive Design**: Works perfectly on desktop and mobile
- **Discord OAuth**: Secure authentication integration

### Discord Bot

- **Slash Commands**: Intuitive command interface
- **DM Notifications**: Personal article digests delivered to your inbox
- **Interactive UI**: Buttons, menus, and pagination
- **Persistent Components**: Works even after bot restarts
- **Multi-server Support**: Can be invited to any Discord server

### Backend API

- **FastAPI**: High-performance async Python framework
- **RESTful Design**: Clean, documented API endpoints
- **JWT Authentication**: Secure token-based auth
- **Background Tasks**: APScheduler for automated jobs
- **Health Checks**: Monitor system status

### AI Integration

- **Groq LLM**: Fast, cost-effective AI processing
- **Dual Models**:
  - Llama 3.1 8B for quick scoring
  - Llama 3.3 70B for detailed analysis
- **Smart Caching**: Articles analyzed once, served many times
- **Rate Limiting**: Automatic API quota management

## 🏗️ Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Next.js Web   │────▶│  FastAPI Backend│────▶│    Supabase     │
│   Dashboard     │     │   + Discord Bot │     │   PostgreSQL    │
└─────────────────┘     └─────────────────┘     └─────────────────┘
        │                       │                         │
        │                       │                         │
        ▼                       ▼                         ▼
  Discord OAuth          Groq LLM API            pgvector Search
  React Query            APScheduler             Multi-tenant Data
```

### Tech Stack

**Frontend**

- Next.js 14 (App Router)
- React 18
- TypeScript
- Tailwind CSS + shadcn/ui
- React Query (TanStack Query)
- Playwright (E2E testing)

**Backend**

- Python 3.11+
- FastAPI 0.111.0+
- discord.py 2.4.0+
- APScheduler 3.10.4+
- pytest + Hypothesis (testing)

**Infrastructure**

- Supabase (PostgreSQL + pgvector)
- Docker + Docker Compose
- Groq Cloud (Llama models)

## 📊 Database Schema

```sql
users                    feeds                   articles
├── id (UUID)           ├── id (UUID)           ├── id (UUID)
├── discord_id          ├── name                ├── feed_id (FK)
├── dm_notifications    ├── url                 ├── title
└── created_at          ├── category            ├── url
                        ├── is_active           ├── published_at
user_subscriptions      └── created_at          ├── tinkering_index
├── id (UUID)                                   ├── ai_summary
├── user_id (FK)        reading_list            ├── embedding (vector)
├── feed_id (FK)        ├── id (UUID)           └── created_at
└── subscribed_at       ├── user_id (FK)
                        ├── article_id (FK)
                        ├── status
                        ├── rating
                        └── updated_at
```

---

## 🔧 Troubleshooting

### Discord Bot Issues

If you encounter errors with Discord bot commands after setup or refactoring:

#### `/news_now` or `/reading_list` Commands Failing

**Symptoms:**

- Bot crashes with database errors
- "Could not find table" errors in logs

**Solution:**

```bash
# 1. Verify bot health
cd backend
python3 scripts/verify_bot_health.py

# 2. Apply missing migrations if needed
python3 scripts/apply_missing_migration.py
```

### Common Issues

**Database Connection Errors:**

- Verify `SUPABASE_URL` and `SUPABASE_KEY` in `.env`
- Check Supabase project is active
- Ensure database tables are created (run migrations)

**Discord Bot Not Responding:**

- Verify `DISCORD_BOT_TOKEN` is correct
- Check bot has proper permissions in Discord server
- Ensure bot is invited with correct OAuth scopes

**Articles Not Fetching:**

- Check scheduler is running: `docker-compose logs -f backend`
- Verify RSS feeds are valid and accessible
- Check Groq API key is valid and has credits

For more help, see the [full documentation](./docs/README.md) or [open an issue](https://github.com/yourusername/tech-news-agent/issues).

---

## 🤝 Contributing

We welcome contributions! Here's how you can help:

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/amazing-feature`
3. **Make your changes** and add tests
4. **Run tests**: `pytest` (backend) and `npm test` (frontend)
5. **Commit**: `git commit -m 'Add amazing feature'`
6. **Push**: `git push origin feature/amazing-feature`
7. **Open a Pull Request**

### Development Guidelines

- Follow existing code style (Black for Python, ESLint for TypeScript)
- Write tests for new features
- Update documentation as needed
- Keep commits atomic and well-described

## 📝 License

MIT License - see [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [Supabase](https://supabase.com) - Database and authentication
- [Groq](https://groq.com) - Fast LLM inference
- [Discord](https://discord.com) - Bot platform and OAuth
- [Vercel](https://vercel.com) - Next.js framework
- [shadcn/ui](https://ui.shadcn.com) - UI components

## 📞 Support

- 📖 [Documentation](./docs/README.md)
- 🐛 [Issue Tracker](https://github.com/yourusername/tech-news-agent/issues)
- 💬 [Discussions](https://github.com/yourusername/tech-news-agent/discussions)

---

**Built with ❤️ for the tech community**
