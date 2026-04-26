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
    deep_summary TEXT,
    deep_summary_generated_at TIMESTAMPTZ,
    embedding VECTOR(1536),
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Create indexes for articles table
CREATE INDEX idx_articles_feed_id ON articles(feed_id);
CREATE INDEX idx_articles_published_at ON articles(published_at);
CREATE INDEX idx_articles_embedding ON articles USING hnsw (embedding vector_cosine_ops);
CREATE INDEX idx_articles_deep_summary ON articles(id) WHERE deep_summary IS NOT NULL;

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

-- Insert default RSS feeds (all verified working URLs)
-- AI & Machine Learning
INSERT INTO feeds (name, url, category, is_active) VALUES 
('Google AI Blog', 'http://googleresearch.blogspot.com/atom.xml', 'AI & Machine Learning', true),
('Simon Willison''s Weblog', 'https://simonwillison.net/atom/everything/', 'AI & Machine Learning', true),
('arXiv cs.AI', 'https://rss.arxiv.org/rss/cs.AI', 'AI & Machine Learning', true),
('MarkTechPost', 'https://www.marktechpost.com/feed/', 'AI & Machine Learning', true),
('MIT Technology Review - AI', 'https://www.technologyreview.com/topic/artificial-intelligence/feed/', 'AI & Machine Learning', true),
('KDnuggets', 'https://www.kdnuggets.com/feed', 'AI & Machine Learning', true);

-- Architecture & System Design
INSERT INTO feeds (name, url, category, is_active) VALUES 
('High Scalability', 'http://feeds.feedburner.com/HighScalability', 'Architecture & System Design', true),
('ByteByteGo', 'https://blog.bytebytego.com/feed', 'Architecture & System Design', true),
('InfoQ', 'https://feed.infoq.com/', 'Architecture & System Design', true),
('Martin Fowler Blog', 'https://martinfowler.com/feed.atom', 'Architecture & System Design', true),
('Netflix Tech Blog', 'https://netflixtechblog.medium.com/feed', 'Architecture & System Design', true),
('ACM Queue', 'https://queue.acm.org/rss/feeds/queuecontent.xml', 'Architecture & System Design', true),
('Stripe Engineering', 'https://stripe.com/blog/feed.rss', 'Architecture & System Design', true);

-- Cloud Native, DevOps & SRE
INSERT INTO feeds (name, url, category, is_active) VALUES 
('Kubernetes Official Blog', 'https://kubernetes.io/feed.xml', 'Cloud Native, DevOps & SRE', true),
('SRE Weekly', 'https://sreweekly.com/feed', 'Cloud Native, DevOps & SRE', true),
('HashiCorp Blog', 'https://www.hashicorp.com/blog/feed.xml', 'Cloud Native, DevOps & SRE', true),
('Cloudflare Blog', 'https://blog.cloudflare.com/rss/', 'Cloud Native, DevOps & SRE', true),
('DZone DevOps', 'https://feeds.dzone.com/devops', 'Cloud Native, DevOps & SRE', true);

-- Cybersecurity & InfoSec
INSERT INTO feeds (name, url, category, is_active) VALUES 
('Krebs on Security', 'https://krebsonsecurity.com/feed/', 'Cybersecurity & InfoSec', true),
('Google Project Zero', 'https://googleprojectzero.blogspot.com/feeds/posts/default', 'Cybersecurity & InfoSec', true),
('Lobsters', 'https://lobste.rs/rss', 'Cybersecurity & InfoSec', true),
('The Morning Paper', 'https://blog.acolyer.org/feed/', 'Cybersecurity & InfoSec', true),
('PortSwigger Research', 'https://portswigger.net/research/rss', 'Cybersecurity & InfoSec', true);

-- Core Programming Languages
INSERT INTO feeds (name, url, category, is_active) VALUES 
('The Rust Blog', 'https://blog.rust-lang.org/feed.xml', 'Core Programming Languages', true),
('This Week in Rust', 'https://this-week-in-rust.org/rss.xml', 'Core Programming Languages', true),
('The Go Blog', 'http://blog.golang.org/feeds/posts/default', 'Core Programming Languages', true),
('Go Weekly', 'https://golangweekly.com/rss/1jn0ck6', 'Core Programming Languages', true);

-- Data Engineering & Analytics
INSERT INTO feeds (name, url, category, is_active) VALUES 
('Seattle Data Guy', 'https://seattledataguy.substack.com/feed', 'Data Engineering & Analytics', true),
('Data Engineering Weekly', 'https://www.dataengineeringweekly.com/feed', 'Data Engineering & Analytics', true),
('Databricks Engineering', 'https://databricks.com/feed', 'Data Engineering & Analytics', true),
('dbt Blog', 'https://www.getdbt.com/blog/rss.xml', 'Data Engineering & Analytics', true),
('Analytics Vidhya', 'https://www.analyticsvidhya.com/feed/', 'Data Engineering & Analytics', true);

-- Web3 & Blockchain Engineering
INSERT INTO feeds (name, url, category, is_active) VALUES 
('Ethereum Foundation Blog', 'https://blog.ethereum.org/feed.xml', 'Web3 & Blockchain Engineering', true),
('Arbitrum (Offchain Labs)', 'https://blog.arbitrum.io/rss/', 'Web3 & Blockchain Engineering', true),
('Polygon Blog', 'https://blog.polygon.technology/feed/', 'Web3 & Blockchain Engineering', true);

-- Frontend & Mobile Development
INSERT INTO feeds (name, url, category, is_active) VALUES 
('Kodeco (Ray Wenderlich)', 'http://www.raywenderlich.com/feed', 'Frontend & Mobile Development', true),
('Smashing Magazine', 'https://www.smashingmagazine.com/feed/', 'Frontend & Mobile Development', true);

-- Web Development & Programming
INSERT INTO feeds (name, url, category, is_active) VALUES 
('freeCodeCamp', 'https://www.freecodecamp.org/news/rss/', 'Web Development & Programming', true),
('CSS-Tricks', 'https://css-tricks.com/feed/', 'Web Development & Programming', true),
('JavaScript Weekly', 'https://javascriptweekly.com/rss', 'Web Development & Programming', true),
('A List Apart', 'https://alistapart.com/main/feed/', 'Web Development & Programming', true),
('Real Python', 'https://realpython.com/atom.xml', 'Web Development & Programming', true),
('Next.js Blog', 'https://nextjs.org/feed.xml', 'Web Development & Programming', true);

-- Official Documentation
INSERT INTO feeds (name, url, category, is_active) VALUES 
('MDN Web Docs Blog', 'https://developer.mozilla.org/en-US/blog/rss.xml', 'Official Documentation', true),
('Node.js Blog', 'https://nodejs.org/en/feed/blog.xml', 'Official Documentation', true),
('React Blog', 'https://react.dev/rss.xml', 'Official Documentation', true),
('Google Developers Blog', 'https://developers.googleblog.com/feeds/posts/default', 'Official Documentation', true);

-- Official Updates
INSERT INTO feeds (name, url, category, is_active) VALUES 
('GitHub Blog', 'https://github.blog/feed/', 'Official Updates', true),
('Vue.js News', 'https://blog.vuejs.org/feed.rss', 'Official Updates', true);

-- Community & Learning
INSERT INTO feeds (name, url, category, is_active) VALUES 
('Stack Overflow Blog', 'https://stackoverflow.blog/feed/', 'Community & Learning', true),
('Dev.to', 'https://dev.to/feed', 'Community & Learning', true);

-- Tech Strategy & Engineering Management
INSERT INTO feeds (name, url, category, is_active) VALUES 
('The Pragmatic Engineer', 'https://blog.pragmaticengineer.com/rss/', 'Tech Strategy & Engineering Management', true),
('Stratechery', 'https://stratechery.com/feed/', 'Tech Strategy & Engineering Management', true);

-- Self-Hosted, FOSS & Privacy
INSERT INTO feeds (name, url, category, is_active) VALUES 
('selfh.st Weekly', 'https://selfh.st/feed/', 'Self-Hosted, FOSS & Privacy', true),
('Home Assistant', 'https://www.home-assistant.io/atom.xml', 'Self-Hosted, FOSS & Privacy', true);

-- Platform Aggregators
INSERT INTO feeds (name, url, category, is_active) VALUES 
('Hacker News Best', 'https://hnrss.org/best', 'Platform Aggregators', true),
('Hacker News Active', 'https://hnrss.org/active', 'Platform Aggregators', true),
('Hacker News Launches', 'https://hnrss.org/launches', 'Platform Aggregators', true),
('Lobsters ML', 'https://lobste.rs/t/ml.rss', 'Platform Aggregators', true),
('TLDR Tech', 'https://tldr.tech/api/rss/tech', 'Platform Aggregators', true),
('Dev.to - System Design', 'https://dev.to/feed/tag/systemdesign', 'Platform Aggregators', true);
