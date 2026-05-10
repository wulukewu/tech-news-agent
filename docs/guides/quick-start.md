# Quick Start Guide

This guide helps you get started with the Tech News Agent project quickly.

## Prerequisites

1. **Supabase Account**: Sign up at [supabase.com](https://supabase.com).
2. **Discord Bot (Optional)**: Set up a bot at [Discord Developers](https://discord.com/developers/applications).
3. **Groq API Key**: Get your key at [console.groq.com](https://console.groq.com).

## Installation

### Option 1: Docker Compose (Recommended)

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/tech-news-agent.git
   cd tech-news-agent
   ```
2. Set up environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your credentials
   ```
3. Initialize the database:
   Run `backend/scripts/init_supabase.sql` in your Supabase SQL Editor.
4. Start the services:
   ```bash
   docker compose up -d
   ```

## First Steps

1. **Web Interface**: Visit `http://localhost:3000` and sign in with Discord OAuth.
2. **Subscribe to Feeds**: Add your favorite RSS feeds from the Subscriptions page.
3. **Trigger Fetch**: Click "Fetch New Articles" in the UI or use `/trigger_fetch` in Discord.
