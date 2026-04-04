# Tech News Agent

An automated technical information curation assistant combining FastAPI, Discord Bot, and Groq LLM. It automatically reads RSS sources from Supabase, scrapes and scores technical articles weekly, stores them in a PostgreSQL database, and sends notifications to Discord.

## Core Features

- **Automated Scraping**: Fetches RSS feeds from Supabase and scrapes articles every Friday at 17:00
- **AI-Powered Scoring**: Evaluates technical value and "tinkering index" using Groq (Llama 3.1 8B)
- **PostgreSQL Storage**: All data stored in Supabase (PostgreSQL) with pgvector support for semantic search
- **Reading List Management**: View, rate (1-5 stars), and manage your reading list directly from Discord with pagination support
- **Smart Recommendations**: Get AI-generated reading recommendations based on your highly-rated articles (4+ stars)
- **Interactive Discord UI**: Filter articles by category, get deep-dive analysis, and manage reading status
- **Persistent Interactive UI**: All buttons and menus work even after bot restarts, ensuring seamless user experience

---

## Prerequisites

### 1. Supabase Database Setup

The project uses Supabase (PostgreSQL) as the primary database with pgvector support for semantic search.

**Setup Steps:**

1. Create a Supabase project at [supabase.com](https://supabase.com)
2. Run the initialization script in the SQL Editor:
   ```bash
   # The script is located at scripts/init_supabase.sql
   ```
3. Run the seed script to populate default RSS feeds:
   ```bash
   python scripts/seed_feeds.py
   ```
4. Get your Supabase URL and API key from Project Settings > API

**Database Schema:**

- `users` - Discord users with multi-tenant support
- `feeds` - RSS feed sources with categories
- `user_subscriptions` - User feed subscriptions
- `articles` - Scraped articles with AI summaries and embeddings
- `reading_list` - User reading lists with ratings and status

### 2. Discord Bot Setup

- Create a Bot at the Discord Developer Portal
- Enable Message Content Intent
- Obtain the Token and invite the Bot to your server
- Obtain the target Channel ID

### 3. API Key

- Obtain an API Key from Groq Cloud

---

## How to Run

### Method 1: Using Docker (Recommended for NAS or Servers)

1. Copy and configure environment variables:

   ```bash
   cp .env.example .env
   ```

   Edit `.env` and fill in your tokens and IDs (see Environment Variables below).

2. Start services:
   ```bash
   docker compose up -d
   ```

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

## Environment Variables

| Variable             | Required | Description                                   |
| -------------------- | -------- | --------------------------------------------- |
| `SUPABASE_URL`       | ✅       | Supabase project URL                          |
| `SUPABASE_KEY`       | ✅       | Supabase API key (anon/service_role)          |
| `DISCORD_TOKEN`      | ✅       | Discord bot token                             |
| `DISCORD_CHANNEL_ID` | ✅       | Discord channel ID for weekly notifications   |
| `GROQ_API_KEY`       | ✅       | Groq Cloud API key                            |
| `TIMEZONE`           | ⚪       | Timezone for scheduler (default: Asia/Taipei) |

---

## Discord Commands

### `/news_now`

Immediately trigger weekly technical news scraping and Discord notification.

**What it does:**

1. Fetches all active RSS feeds from Supabase
2. Scrapes articles from the past 7 days
3. Evaluates each article's technical value and "tinkering index" using AI
4. Sends a notification to Discord with interactive buttons

**Interactive Elements:**

- **📋 Filter Menu**: Select a category to filter articles instantly
- **📖 Deep Dive Buttons**: Get detailed AI-generated technical analysis (up to 5 articles)

**Note:** Some features are still in development (Read Later, Mark as Read).

### `/reading_list view`

View and manage your reading list directly in Discord.

**Features:**

- **Pagination**: Browse articles 5 at a time with Previous/Next buttons
- **Mark as Read**: Click ✅ button to mark any article as read
- **Rate Articles**: Use dropdown menus to rate articles 1-5 stars (⭐)
- **Ephemeral**: Only you can see your reading list (private responses)

**Display Format:**
Each article shows:

- Title and URL
- Category
- Current rating (or "未評分" if unrated)

### `/reading_list recommend`

Get AI-generated reading recommendations based on your highly-rated articles (4+ stars).

**How it works:**

1. Fetches all articles you've rated 4 or 5 stars
2. Analyzes titles and categories
3. Generates a personalized recommendation summary in Traditional Chinese
4. Suggests what to read next based on your interests

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

## Testing

### Supabase Database Tests

The Supabase database infrastructure has comprehensive test coverage with property-based testing.

**Run all Supabase tests:**

```bash
pytest tests/test_database_properties.py tests/test_config.py tests/test_seed_feeds.py tests/test_sql_init_integration.py -v
```

**Test categories:**

- **Configuration tests** (`test_config.py`): Verify Supabase config fields
- **SQL initialization tests** (`test_sql_init_integration.py`): Verify database schema creation
- **Seed script tests** (`test_seed_feeds.py`): Verify RSS feed seeding
- **Property-based tests** (`test_database_properties.py`): 17 correctness properties using Hypothesis

**Property-based tests validate:**

- CASCADE DELETE behavior (users, feeds, articles)
- UNIQUE constraints (discord_id, URLs, subscriptions)
- NOT NULL constraints (required fields)
- CHECK constraints (status values, rating ranges)
- Timestamp auto-population
- Database triggers (updated_at)
- Seed script behavior

**Adjust test speed:**

```bash
# Fast (10 examples per property)
HYPOTHESIS_PROFILE=dev pytest tests/test_database_properties.py -v

# Default (20 examples per property)
pytest tests/test_database_properties.py -v

# CI/Production (100 examples per property)
HYPOTHESIS_PROFILE=ci pytest tests/test_database_properties.py -v
```

### Documentation

For detailed testing documentation, see:

- [Supabase Testing Guide](./docs/testing/supabase-migration-testing.md) - Complete testing guide
- [Test Fixtures Guide](./docs/testing/test-fixtures.md) - Fixture usage and examples
- [Cleanup Mechanism Guide](./docs/testing/cleanup-mechanism.md) - Test data cleanup
- [SQL Integration Tests Guide](./docs/testing/sql-integration-tests.md) - SQL initialization tests

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

## Project Structure

```text
tech-news-agent/
├── .github/
│   └── workflows/
│       └── ci.yml           # GitHub Actions CI configuration
├── .hypothesis/             # Hypothesis property-based testing cache
├── .kiro/
│   └── specs/               # Feature specifications and design documents
├── app/
│   ├── bot/
│   │   ├── cogs/
│   │   │   ├── interactions.py     # Interactive UI components (buttons, menus, views)
│   │   │   ├── news_commands.py    # /news_now command
│   │   │   └── reading_list.py     # /reading_list command group
│   │   └── client.py        # Discord bot client with persistent view registration
│   ├── core/
│   │   ├── config.py        # Environment variable settings (Pydantic BaseSettings)
│   │   └── exceptions.py    # Custom exception classes
│   ├── schemas/
│   │   └── article.py       # Pydantic models (ArticleSchema, ReadingListItem, etc.)
│   ├── services/
│   │   ├── llm_service.py   # Groq LLM integration (scoring, summaries, recommendations)
│   │   ├── supabase_service.py # Supabase database service
│   │   └── rss_service.py   # RSS feed fetching and parsing
│   ├── tasks/
│   │   └── scheduler.py     # APScheduler weekly automation
│   └── main.py              # FastAPI entry point and lifecycle management
├── docs/                    # Documentation
│   └── testing/             # Testing documentation
│       ├── supabase-migration-testing.md  # Supabase testing guide
│       ├── test-fixtures.md               # Test fixtures guide
│       ├── cleanup-mechanism.md           # Cleanup mechanism guide
│       └── sql-integration-tests.md       # SQL integration tests guide
├── logs/                    # Application logs directory
├── scripts/                 # Database and utility scripts
│   ├── init_supabase.sql    # Supabase database initialization script
│   └── seed_feeds.py        # RSS feed seeding script
├── tests/                   # Unit, property-based, and integration tests
│   ├── conftest.py          # Pytest fixtures and configuration
│   ├── test_config.py       # Supabase configuration tests
│   ├── test_database_properties.py  # Property-based tests (17 properties)
│   ├── test_seed_feeds.py   # Seed script tests
│   ├── test_sql_init_integration.py # SQL initialization tests
│   └── ...                  # Other tests
├── .env.example             # Example environment variables
├── .gitignore
├── docker-compose.yml       # Docker Compose configuration
├── Dockerfile               # Docker image definition
├── pytest.ini               # Pytest configuration
├── README.md                # English documentation
├── README_zh.md             # Chinese documentation
├── requirements.txt         # Production dependencies
└── requirements-dev.txt     # Development dependencies
```

---

## Feature Highlights

### 🎯 Smart Article Curation

- AI evaluates each article's technical depth and "tinkering index"
- Only the most valuable content makes it to your digest
- Automatic categorization by topic

### 📚 Comprehensive Reading Management

- Rate articles to build your preference profile
- Get personalized recommendations based on your ratings
- Track reading status in Supabase

### 🗄️ PostgreSQL + pgvector

- All data stored in Supabase (PostgreSQL)
- pgvector support for future semantic search features
- Efficient indexing with HNSW algorithm

### ⚡ Interactive Discord Experience

- Filter articles by category instantly
- Get deep-dive analysis on demand
- Manage your reading list without leaving Discord
- All interactions work even after bot restarts

### 🤖 Powered by AI

- **Groq Llama 3.1 8B**: Fast article evaluation and scoring
- **Groq Llama 3.3 70B**: High-quality summaries and recommendations
- Traditional Chinese output for all AI-generated content

---

## Tips & Best Practices

1. **Set up categories consistently**: Use the same category names across feeds for better filtering
2. **Rate articles regularly**: Build up your rating history for better recommendations
3. **Use Deep Dive sparingly**: Each deep dive costs API tokens, use it for articles you're genuinely interested in
4. **Customize the schedule**: Edit `scheduler.py` to change the weekly scraping time (default: Friday 17:00)

---

## Troubleshooting

**Bot doesn't respond to commands:**

- Check that the bot has proper permissions in your Discord server
- Verify `DISCORD_TOKEN` is correct
- Check bot logs for errors

**Buttons don't work after bot restart:**

- This is expected for old messages created before persistent views were implemented
- New messages created after the bot restart will have working buttons

**Database connection errors:**

- Verify `SUPABASE_URL` and `SUPABASE_KEY` are set correctly
- Check that your Supabase project is active
- Ensure database schema is initialized (run `scripts/init_supabase.sql`)

**Reading list shows no articles:**

- Check that articles in reading_list table have status = 'Unread'
- Verify you've added articles to your reading list

**Recommendations not working:**

- You need at least one article rated 4 or 5 stars
- Check `GROQ_API_KEY` is valid and has quota remaining

---

## License

MIT
