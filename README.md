# Tech News Agent

An automated technical information curation assistant combining FastAPI, Discord Bot, and Groq LLM. It automatically reads RSS sources from Notion, scrapes and scores technical articles weekly, builds a rich Notion weekly digest page, and sends a lightweight summary notification to Discord.

## Core Features

- Automated Scraping: Fetches RSS feeds from Notion and scrapes articles every Friday at 17:00.
- Hardcore Scoring: Evaluates technical value and "tinkering index" using Groq (Llama 3.1 8B).
- Independent Article Pages: Each curated article gets its own Notion page in the Weekly Digests database for better management and tracking.
- Reading Status Management: Track article reading status (Unread/Read/Archived) and mark articles as read directly from Discord.
- Simplified Discord Notification: Sends article list with Notion page links for each article, making it easy to jump to individual articles.
- Bidirectional Interaction: Supports `/news_now` slash command and UI buttons (Mark as Read, Filter, Deep Dive, Save to Read Later).

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

| Column Name       | Type   | Notes                                    |
| ----------------- | ------ | ---------------------------------------- |
| `Title`           | Title  | Rename the default "Name" column to this |
| `URL`             | URL    |                                          |
| `Added_At`        | Date   |                                          |
| `Source_Category` | Select |                                          |
| `Status`          | Status | Must have an option named `Unread`       |

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

| Variable                      | Required | Description                                  |
| ----------------------------- | -------- | -------------------------------------------- |
| `NOTION_TOKEN`                | ✅       | Notion integration token                     |
| `NOTION_FEEDS_DB_ID`          | ✅       | Notion Feeds database ID                     |
| `NOTION_READ_LATER_DB_ID`     | ✅       | Notion Read Later database ID                |
| `NOTION_WEEKLY_DIGESTS_DB_ID` | ✅       | Notion Weekly Digests database ID (required) |
| `DISCORD_TOKEN`               | ✅       | Discord bot token                            |
| `DISCORD_CHANNEL_ID`          | ✅       | Discord channel ID for weekly notifications  |
| `GROQ_API_KEY`                | ✅       | Groq Cloud API key                           |

---

## Discord Commands

- `/news_now`: Immediately trigger weekly technical news scraping, Notion digest creation, and Discord notification.
- `/add_feed`: Quickly add an RSS feed to the Notion Feeds database.

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
   - A new page appears in your Notion Weekly Digests database with title `週報 YYYY-WW`.
   - The page contains Toggle blocks grouped by category, each with Bookmark + Callout children.
   - Discord receives a notification with stats, Top 5 article links, and the Notion page URL.

### Degradation Test

Leave `NOTION_WEEKLY_DIGESTS_DB_ID` empty in `.env`, then trigger `/news_now`. Discord should send a notification containing `（Notion 頁面建立失敗，請查看日誌）` instead of a Notion link.

---

## Project Structure

```text
tech-news-agent/
├── app/
│   ├── main.py              # FastAPI entry point and lifecycle management
│   ├── bot/                 # Discord Bot logic and slash commands
│   ├── services/            # Core services (Notion, RSS, LLM)
│   │   ├── notion_service.py  # Includes Digest Builder methods
│   │   ├── llm_service.py     # Includes generate_digest_intro
│   │   └── rss_service.py
│   ├── schemas/             # Pydantic data schemas (incl. WeeklyDigestResult)
│   ├── tasks/               # APScheduler background tasks
│   │   └── scheduler.py       # weekly_news_job + build_discord_notification
│   └── core/                # Config and exceptions
└── tests/                   # Unit, property, and integration tests
```
