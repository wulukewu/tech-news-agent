# Tech News Agent

An automated technical information curation assistant combining FastAPI, Discord Bot, and Groq LLM. It automatically reads RSS sources from Notion, scrapes and scores technical articles weekly, and broadcasts curated Markdown newsletters via Discord.

## Core Features
*   Automated Scraping: Automatically fetches RSS feeds from Notion and scrapes articles every Friday at 17:00.
*   Hardcore Scoring: Evaluates technical value and "tinkering index" using Groq (Llama 3.1 8B).
*   Curated Reports: Automatically filters marketing fluff and generates geek-style newsletters using Llama 3.3 70B.
*   Bidirectional Interaction: Supports Discord slash commands (/news_now) and UI buttons (one-click save to Notion Read Later).

---

## Prerequisites

### 1. Notion Database Setup
Create two databases and add your Notion Integration (Connect) to their permissions:
*   Feeds Database:
    *   Name (Title)
    *   URL (URL)
    *   Category (Select)
    *   Is_Active (Checkbox)
*   Read Later Database (Optional, for button functionality):
    *   Title (Title)
    *   URL (URL)
    *   Added_At (Date)
    *   Source_Category (Select)
    *   Status (Status: Unread/Read)

### 2. Discord Bot Setup
*   Create a Bot at the Discord Developer Portal.
*   Enable Message Content Intent.
*   Obtain the Token and invite the Bot to your server.
*   Obtain the target Channel ID.

### 3. API Key
*   Obtain an API Key from Groq Cloud.

---

## How to Run

### Method 1: Using Docker (Recommended for NAS or Servers)
1.  Copy and configure environment variables:
    ```bash
    cp .env.example .env
    ```
    Edit .env and fill in your tokens and IDs.

2.  Start services:
    ```bash
    docker compose up -d
    ```

### Method 2: Local Python Execution
1.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

2.  Configure environment variables (create .env).

3.  Start the application:
    ```bash
    python -m app.main
    ```

---

## Discord Commands
*   /news_now: Immediately trigger weekly technical news scraping and generation.
*   /add_feed: (In Development) Quickly add an RSS feed to Notion.

## Project Structure
```text
tech-news-agent/
├── app/
│   ├── main.py          # FastAPI entry point and lifecycle management
│   ├── bot/             # Discord Bot logic
│   ├── services/        # Core services (Notion, RSS, LLM)
│   ├── schemas/         # Pydantic data schemas
│   └── tasks/           # APScheduler background tasks
└── ...
```