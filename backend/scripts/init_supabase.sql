-- Supabase Migration Phase 1: Database Initialization Script
-- This script creates the complete database structure for Tech News Agent
-- Execute this script in Supabase Dashboard > SQL Editor

-- Enable pgvector extension for vector similarity search
CREATE EXTENSION IF NOT EXISTS vector;

-- Create users table
-- Stores system users identified by Discord ID
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    discord_id TEXT UNIQUE NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Create feeds table
-- Global RSS feed pool shared across all users
CREATE TABLE feeds (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    url TEXT UNIQUE NOT NULL,
    category TEXT NOT NULL,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Create indexes for feeds table
CREATE INDEX idx_feeds_is_active ON feeds(is_active);
CREATE INDEX idx_feeds_category ON feeds(category);

-- Create user_subscriptions table
-- Links users to their subscribed feeds (many-to-many relationship)
CREATE TABLE user_subscriptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    feed_id UUID REFERENCES feeds(id) ON DELETE CASCADE,
    subscribed_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE(user_id, feed_id)
);

-- Create indexes for user_subscriptions table
CREATE INDEX idx_user_subscriptions_user_id ON user_subscriptions(user_id);
CREATE INDEX idx_user_subscriptions_feed_id ON user_subscriptions(feed_id);

-- Create articles table
-- Global article pool fetched from RSS feeds
CREATE TABLE articles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    feed_id UUID REFERENCES feeds(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    url TEXT UNIQUE NOT NULL,
    published_at TIMESTAMPTZ,
    tinkering_index INTEGER,
    ai_summary TEXT,
    embedding VECTOR(1536),
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Create indexes for articles table
CREATE INDEX idx_articles_feed_id ON articles(feed_id);
CREATE INDEX idx_articles_published_at ON articles(published_at);
CREATE INDEX idx_articles_embedding ON articles USING hnsw (embedding vector_cosine_ops);

-- Create reading_list table
-- User's personal reading list and interaction records
CREATE TABLE reading_list (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    article_id UUID REFERENCES articles(id) ON DELETE CASCADE,
    status TEXT CHECK (status IN ('Unread', 'Read', 'Archived')),
    rating INTEGER CHECK (rating >= 1 AND rating <= 5),
    added_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE(user_id, article_id)
);

-- Create indexes for reading_list table
CREATE INDEX idx_reading_list_user_id ON reading_list(user_id);
CREATE INDEX idx_reading_list_status ON reading_list(status);
CREATE INDEX idx_reading_list_rating ON reading_list(rating);

-- Create function to automatically update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create trigger to update updated_at on reading_list modifications
CREATE TRIGGER update_reading_list_updated_at
    BEFORE UPDATE ON reading_list
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
