# Tech News Agent

An automated technical information curation assistant combining FastAPI, Discord Bot, and Groq LLM. It automatically reads RSS sources from Notion, scrapes and scores technical articles weekly, builds a rich Notion weekly digest page, and sends a lightweight summary notification to Discord.

## Core Features

- **Automated Scraping**: Fetches RSS feeds from Notion and scrapes articles every Friday at 17:00.
- **Hardcore Scoring**: Evaluates technical value and "tinkering index" using Groq (Llama 3.1 8B).
- **Independent Article Pages**: Each curated article gets its own Notion page in the Weekly Digests database for better management and tracking.
- **Reading Status Management**: Track article reading status (Unread/Read/Archived) and mark articles as read directly from Discord.
- **Interactive Filtering**: Filter articles by category using Discord select menus with real-time results.
- **Deep Dive Summaries**: Get LLM-generated detailed technical analysis for any article with one click.
- **Reading List Management**: View, rate (1-5 stars), and manage your Notion Read Later database directly from Discord with pagination support.
- **Smart Recommendations**: Get AI-generated reading recommendations based on your highly-rated articles (4+ stars).
- **Persistent Interactive UI**: All buttons and menus work even after bot restarts, ensuring seamless user experience.
- **Bidirectional Interaction**: Full two-way sync between Discord and Notion for article management.

---

## Prerequisites

### 1. Notion Database Setup

Create three databases and add your Notion Integration (Connect) to their permissions.

> ⚠️ Column names are case-sensitive and must match exactly.

**Feeds Database** (stores RSS sources):

| Column Name | Type     | Notes                         |
| ----------- | -------- | ----------------------------- |
| `Name`      | Title    | Default title column          |
| `URL`       | URL      |                               |
| `Category`  | Select   | e.g. DevOps, AI, Security     |
| `Active`    | Checkbox | Only checked rows are fetched |

**Read Later Database** (stores saved articles via Discord button):

| Column Name       | Type   | Notes                                                      |
| ----------------- | ------ | ---------------------------------------------------------- |
| `Title`           | Title  | Rename the default "Name" column to this                   |
| `URL`             | URL    |                                                            |
| `Added_At`        | Date   |                                                            |
| `Source_Category` | Select |                                                            |
| `Status`          | Status | Must have an option named `Unread`                         |
| `Rating`          | Number | Article rating 1-5 (optional, for `/reading_list` feature) |

**Weekly Digests Database** (stores individual article pages):

| Column Name       | Type   | Notes                                        |
| ----------------- | ------ | -------------------------------------------- |
| `Title`           | Title  | Article title                                |
| `URL`             | URL    | Original article link                        |
| `Source_Category` | Select | Article category (e.g. AI, DevOps, Security) |
| `Published_Week`  | Text   | Publication week in ISO format (YYYY-WW)     |
| `Tinkering_Index` | Number | Tinkering index (1-5)                        |
| `Status`          | Status | Reading status (Unread / Read / Archived)    |
| `Added_At`        | Date   | Date when article was added                  |

### 2. Discord Bot Setup

- Create a Bot at the Discord Developer Portal.
- Enable Message Content Intent.
- Obtain the Token and invite the Bot to your server.
- Obtain the target Channel ID.

### 3. API Key

- Obtain an API Key from Groq Cloud.

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

| Variable                      | Required | Description                                   |
| ----------------------------- | -------- | --------------------------------------------- |
| `NOTION_TOKEN`                | ✅       | Notion integration token                      |
| `NOTION_FEEDS_DB_ID`          | ✅       | Notion Feeds database ID                      |
| `NOTION_READ_LATER_DB_ID`     | ✅       | Notion Read Later database ID                 |
| `NOTION_WEEKLY_DIGESTS_DB_ID` | ✅       | Notion Weekly Digests database ID             |
| `DISCORD_TOKEN`               | ✅       | Discord bot token                             |
| `DISCORD_CHANNEL_ID`          | ✅       | Discord channel ID for weekly notifications   |
| `GROQ_API_KEY`                | ✅       | Groq Cloud API key                            |
| `TIMEZONE`                    | ⚪       | Timezone for scheduler (default: Asia/Taipei) |

---

## Discord Commands

### `/news_now`

Immediately trigger weekly technical news scraping, Notion digest creation, and Discord notification.

**What it does:**

1. Fetches all active RSS feeds from your Notion Feeds database
2. Scrapes articles from the past 7 days
3. Evaluates each article's technical value and "tinkering index" using AI
4. Creates individual Notion pages for each curated article in Weekly Digests database
5. Sends a notification to Discord with interactive buttons

**Interactive Elements:**

- **📋 Filter Menu**: Select a category to filter articles instantly
- **📖 Deep Dive Buttons**: Get detailed AI-generated technical analysis (up to 5 articles)
- **⭐ Read Later Buttons**: Save articles to your Notion Read Later database (up to 10 articles)
- **✅ Mark as Read Buttons**: Mark articles as read in Notion (up to 5 articles)

### `/add_feed`

Quickly add a new RSS feed to your Notion Feeds database.

**Parameters:**

- `name`: Feed name (e.g., "Hacker News")
- `url`: RSS/Atom feed URL
- `category`: Category for organization (e.g., "AI", "DevOps", "Security")

**Example:**

```
/add_feed name:TechCrunch url:https://techcrunch.com/feed/ category:Tech News
```

### `/reading_list view`

View and manage your Notion Read Later database directly in Discord.

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

### Read Later Buttons

- **Location**: Up to 10 buttons per `/news_now` notification
- **Label**: ⭐ 稍後閱讀 followed by article title
- **Function**: Saves article to your Notion Read Later database
- **Behavior**: Button disables after successful save
- **Response**: Ephemeral confirmation message

### Mark as Read Buttons

- **Location**: Up to 5 buttons per `/news_now` notification
- **Label**: ✅ followed by article title
- **Function**: Updates article status to "Read" in Notion Weekly Digests database
- **Behavior**: Button disables after successful update
- **Response**: Ephemeral confirmation message

### Rating Select Menus

- **Location**: In `/reading_list view` pagination interface
- **Options**: ⭐ (1 star) through ⭐⭐⭐⭐⭐ (5 stars)
- **Function**: Rate articles in your Read Later database
- **Use Case**: Build your reading preferences for personalized recommendations

---

## Article Management System

### Individual Article Pages

Each curated article gets its own dedicated Notion page in the Weekly Digests database with:

**Page Properties:**

- **Title**: Article title
- **URL**: Original article link
- **Source_Category**: Article category (AI, DevOps, Security, etc.)
- **Published_Week**: ISO week format (YYYY-WW, e.g., "2025-28")
- **Tinkering_Index**: Technical complexity score (1-5)
- **Status**: Reading status (Unread / Read / Archived)
- **Added_At**: Date when article was added

**Page Content:**

- 💡 **Callout**: AI-generated recommendation reason
- 🎯 **Callout**: Actionable takeaway (if available)
- 🔖 **Bookmark**: Direct link to the original article

### Reading Status Tracking

Track your reading progress across three states:

- **Unread**: Newly added articles (default)
- **Read**: Articles you've finished reading
- **Archived**: Articles you want to keep but remove from active lists

Update status via:

- Discord "✅ Mark as Read" buttons
- `/reading_list view` interface
- Directly in Notion

### Weekly Digest Notifications

When `/news_now` runs (or via scheduled task), you receive a Discord notification with:

**Statistics:**

```
本週技術週報已發布

本週統計：抓取 42 篇，精選 7 篇

精選文章：
1. [AI] Building a RAG System with Rust
   https://notion.so/abc123
2. [DevOps] Kubernetes 1.30 新功能解析
   https://notion.so/def456
...
```

**Features:**

- Lists all curated articles with Notion page links
- Shows total articles fetched vs. curated
- Automatically truncates if over 2000 characters
- Includes interactive buttons for immediate action

---

## Testing

### Unit & Property Tests (no real API needed)

```bash
python -m pytest tests/ -v
```

To run only the Notion Weekly Digest feature tests:

```bash
python -m pytest tests/test_notion_digest_builder.py tests/test_notion_service_digest.py tests/test_llm_digest_intro.py tests/test_discord_notifier.py tests/test_scheduler_integration.py -v
```

Property-based tests use [Hypothesis](https://hypothesis.readthedocs.io/) and run 100 iterations each to verify correctness properties like message length limits, block structure, and ISO week title format.

### Manual End-to-End Test

1. Fill in all environment variables in `.env` including `NOTION_WEEKLY_DIGESTS_DB_ID`.
2. Run the bot and trigger `/news_now` in Discord.
3. Verify:
   - Individual article pages appear in your Notion Weekly Digests database
   - Each page has correct properties (Title, URL, Category, Published_Week, Status, etc.)
   - Discord receives a notification with stats and article links
   - Interactive buttons work:
     - Filter menu filters by category
     - Deep Dive buttons generate AI summaries
     - Read Later buttons save to Notion
     - Mark as Read buttons update article status
4. Test `/reading_list view`:
   - Verify pagination works (Previous/Next buttons)
   - Test Mark as Read buttons
   - Test rating dropdowns (1-5 stars)
5. Test `/reading_list recommend`:
   - Rate some articles 4-5 stars first
   - Verify AI-generated recommendations appear
6. Test `/add_feed`:
   - Add a new RSS feed
   - Verify it appears in Notion Feeds database with Active=true

### Interactive UI Persistence Test

1. Trigger `/news_now` and note the message with buttons
2. Restart the bot
3. Click buttons on the old message
4. Verify all buttons still work correctly (this tests persistent views)

### Degradation Test

Leave `NOTION_WEEKLY_DIGESTS_DB_ID` empty in `.env`, then trigger `/news_now`. The bot should handle the error gracefully and inform you that article page creation failed.

---

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
│   │   │   ├── news_commands.py    # /news_now and /add_feed commands
│   │   │   └── reading_list.py     # /reading_list command group
│   │   └── client.py        # Discord bot client with persistent view registration
│   ├── core/
│   │   ├── config.py        # Environment variable settings (Pydantic BaseSettings)
│   │   └── exceptions.py    # Custom exception classes
│   ├── schemas/
│   │   └── article.py       # Pydantic models (ArticleSchema, ReadingListItem, etc.)
│   ├── services/
│   │   ├── llm_service.py   # Groq LLM integration (scoring, summaries, recommendations)
│   │   ├── notion_service.py # Notion API integration (articles, feeds, reading list)
│   │   └── rss_service.py   # RSS feed fetching and parsing
│   ├── tasks/
│   │   └── scheduler.py     # APScheduler weekly automation
│   └── main.py              # FastAPI entry point and lifecycle management
├── logs/                    # Application logs directory
├── tests/                   # Unit, property-based, and integration tests
│   ├── test_article_page_result.py
│   ├── test_bug_conditions.py
│   ├── test_build_article_list_notification.py
│   ├── test_build_week_string.py
│   ├── test_interactions.py
│   ├── test_llm_service.py
│   ├── test_mark_read_view.py
│   ├── test_notion_service_create_article_page.py
│   ├── test_notion_service_mark_article_as_read.py
│   ├── test_notion_service.py
│   ├── test_preservation.py
│   ├── test_reading_list.py
│   ├── test_rss_service.py
│   ├── test_startup_validation.py
│   ├── test_weekly_news_job_integration.py
│   └── test_weekly_news_job_property.py
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

- Save articles for later with one click
- Rate articles to build your preference profile
- Get personalized recommendations based on your ratings
- Track reading status across Discord and Notion

### 🎨 Rich Notion Integration

- Individual pages for each article with AI-generated insights
- Structured organization by week and category
- Full-text search and filtering in Notion
- Bidirectional sync with Discord

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
4. **Check Notion for full content**: Discord shows summaries, but Notion pages have complete AI analysis
5. **Customize the schedule**: Edit `scheduler.py` to change the weekly scraping time (default: Friday 17:00)

---

## Troubleshooting

**Bot doesn't respond to commands:**

- Check that the bot has proper permissions in your Discord server
- Verify `DISCORD_TOKEN` is correct
- Check bot logs for errors

**Buttons don't work after bot restart:**

- This is expected for old messages created before persistent views were implemented
- New messages created after the bot restart will have working buttons

**Notion pages not created:**

- Verify `NOTION_WEEKLY_DIGESTS_DB_ID` is set correctly
- Check that your Notion integration has access to the database
- Ensure all required columns exist in the database

**Reading list shows no articles:**

- Check that articles in Read Later database have Status = "Unread"
- Verify `NOTION_READ_LATER_DB_ID` is correct

**Recommendations not working:**

- You need at least one article rated 4 or 5 stars
- Check `GROQ_API_KEY` is valid and has quota remaining

---

## Project Structure

```text
tech-news-agent/
├── .github/
│   └── workflows/
│       └── ci.yml           # GitHub Actions CI configuration
├── app/
│   ├── bot/
│   │   ├── cogs/
│   │   │   ├── interactions.py     # Interactive UI components (buttons, menus, views)
│   │   │   ├── news_commands.py    # /news_now and /add_feed commands
│   │   │   └── reading_list.py     # /reading_list command group
│   │   └── client.py        # Discord bot client with persistent view registration
│   ├── core/
│   │   ├── config.py        # Environment variable settings (Pydantic BaseSettings)
│   │   └── exceptions.py    # Custom exception classes
│   ├── schemas/
│   │   └── article.py       # Pydantic models (ArticleSchema, ReadingListItem, etc.)
│   ├── services/
│   │   ├── llm_service.py   # Groq LLM integration (scoring, summaries, recommendations)
│   │   ├── notion_service.py # Notion API integration (articles, feeds, reading list)
│   │   └── rss_service.py   # RSS feed fetching and parsing
│   ├── tasks/
│   │   └── scheduler.py     # APScheduler weekly automation
│   └── main.py              # FastAPI entry point and lifecycle management
├── logs/                    # Application logs directory
├── tests/                   # Unit, property-based, and integration tests
│   ├── test_article_page_result.py
│   ├── test_bug_conditions.py
│   ├── test_build_article_list_notification.py
│   ├── test_build_week_string.py
│   ├── test_interactions.py
│   ├── test_llm_service.py
│   ├── test_mark_read_view.py
│   ├── test_notion_service_create_article_page.py
│   ├── test_notion_service_mark_article_as_read.py
│   ├── test_notion_service.py
│   ├── test_preservation.py
│   ├── test_reading_list.py
│   ├── test_rss_service.py
│   ├── test_startup_validation.py
│   ├── test_weekly_news_job_integration.py
│   └── test_weekly_news_job_property.py
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
