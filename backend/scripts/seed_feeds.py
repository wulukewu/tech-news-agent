#!/usr/bin/env python3
"""
Seed script for initializing default RSS feeds in Supabase database.

This script:
1. Loads environment variables from .env file
2. Validates required Supabase credentials
3. Establishes connection to Supabase
4. Inserts predefined RSS feeds into the feeds table

Usage:
    python scripts/seed_feeds.py
"""

import os

from dotenv import load_dotenv
from supabase import Client, create_client


def main():
    """Main function to seed feeds into Supabase database."""

    # Load environment variables from .env file
    load_dotenv()

    # Validate required environment variables
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")

    if not supabase_url:
        raise ValueError(
            "Error: Missing required environment variable: SUPABASE_URL\n"
            "Please copy .env.example to .env and fill in the values"
        )

    if not supabase_key:
        raise ValueError(
            "Error: Missing required environment variable: SUPABASE_KEY\n"
            "Please copy .env.example to .env and fill in the values"
        )

    # Create Supabase client connection
    try:
        supabase: Client = create_client(supabase_url, supabase_key)
        print("Successfully connected to Supabase")
    except Exception as e:
        raise ConnectionError(
            f"Error: Failed to connect to Supabase\n"
            f"Please check:\n"
            f"1. SUPABASE_URL is correct (format: https://xxx.supabase.co)\n"
            f"2. SUPABASE_KEY is valid (check Supabase Dashboard > Settings > API)\n"
            f"3. Network connection is available\n"
            f"Details: {e!s}"
        )

    # Define default RSS feeds data structure (all verified working URLs)
    default_feeds = [
        # AI & Machine Learning
        {
            "name": "Google AI Blog",
            "url": "http://googleresearch.blogspot.com/atom.xml",
            "category": "AI & Machine Learning",
            "is_active": True,
        },
        {
            "name": "Simon Willison's Weblog",
            "url": "https://simonwillison.net/atom/everything/",
            "category": "AI & Machine Learning",
            "is_active": True,
        },
        {
            "name": "MIT Technology Review - AI",
            "url": "https://www.technologyreview.com/topic/artificial-intelligence/feed/",
            "category": "AI & Machine Learning",
            "is_active": True,
        },
        # Research & Academia
        {
            "name": "OpenAI Engineering",
            "url": "https://openai.com/news/engineering/rss.xml",
            "category": "Research & Academia",
            "is_active": True,
        },
        # Individual Engineers & Thought Leaders
        {
            "name": "Lil'Log (Lilian Weng)",
            "url": "https://lilianweng.github.io/lil-log/feed.xml",
            "category": "Individual Engineers & Thought Leaders",
            "is_active": True,
        },
        # Architecture & System Design
        {
            "name": "ByteByteGo",
            "url": "https://blog.bytebytego.com/feed",
            "category": "Architecture & System Design",
            "is_active": True,
        },
        {
            "name": "High Scalability",
            "url": "http://feeds.feedburner.com/HighScalability",
            "category": "Architecture & System Design",
            "is_active": True,
        },
        {
            "name": "Martin Fowler Blog",
            "url": "https://martinfowler.com/feed.atom",
            "category": "Architecture & System Design",
            "is_active": True,
        },
        {
            "name": "ACM Queue",
            "url": "https://queue.acm.org/rss/feeds/queuecontent.xml",
            "category": "Architecture & System Design",
            "is_active": True,
        },
        {
            "name": "Netflix Tech Blog",
            "url": "https://netflixtechblog.medium.com/feed",
            "category": "Architecture & System Design",
            "is_active": True,
        },
        {
            "name": "Stripe Engineering",
            "url": "https://stripe.com/blog/feed.rss",
            "category": "Architecture & System Design",
            "is_active": True,
        },
        # Cloud Native, DevOps & SRE
        {
            "name": "Cloudflare Blog",
            "url": "https://blog.cloudflare.com/rss/",
            "category": "Cloud Native, DevOps & SRE",
            "is_active": True,
        },
        {
            "name": "Kubernetes Official Blog",
            "url": "https://kubernetes.io/feed.xml",
            "category": "Cloud Native, DevOps & SRE",
            "is_active": True,
        },
        {
            "name": "SRE Weekly",
            "url": "https://sreweekly.com/feed",
            "category": "Cloud Native, DevOps & SRE",
            "is_active": True,
        },
        {
            "name": "HashiCorp Blog",
            "url": "https://www.hashicorp.com/blog/feed.xml",
            "category": "Cloud Native, DevOps & SRE",
            "is_active": True,
        },
        # Engineering Blogs - Big Tech
        {
            "name": "Uber Engineering",
            "url": "https://www.uber.com/blog/engineering/rss/",
            "category": "Engineering Blogs - Big Tech",
            "is_active": True,
        },
        {
            "name": "Slack Engineering",
            "url": "https://slack.engineering/feed",
            "category": "Engineering Blogs - Big Tech",
            "is_active": True,
        },
        {
            "name": "Spotify Engineering",
            "url": "https://engineering.atspotify.com/feed/",
            "category": "Engineering Blogs - Big Tech",
            "is_active": True,
        },
        {
            "name": "Engineering at Meta",
            "url": "https://engineering.fb.com/feed/",
            "category": "Engineering Blogs - Big Tech",
            "is_active": True,
        },
        # Open Source & Developer Tools
        {
            "name": "AWS Blog",
            "url": "https://aws.amazon.com/blogs/aws/feed/",
            "category": "Open Source & Developer Tools",
            "is_active": True,
        },
        # Cybersecurity & InfoSec
        {
            "name": "Krebs on Security",
            "url": "https://krebsonsecurity.com/feed/",
            "category": "Cybersecurity & InfoSec",
            "is_active": True,
        },
        {
            "name": "Google Project Zero",
            "url": "https://googleprojectzero.blogspot.com/feeds/posts/default",
            "category": "Cybersecurity & InfoSec",
            "is_active": True,
        },
        {
            "name": "PortSwigger Research",
            "url": "https://portswigger.net/research/rss",
            "category": "Cybersecurity & InfoSec",
            "is_active": True,
        },
        # Core Programming Languages
        {
            "name": "The Rust Blog",
            "url": "https://blog.rust-lang.org/feed.xml",
            "category": "Core Programming Languages",
            "is_active": True,
        },
        {
            "name": "This Week in Rust",
            "url": "https://this-week-in-rust.org/rss.xml",
            "category": "Core Programming Languages",
            "is_active": True,
        },
        {
            "name": "The Go Blog",
            "url": "http://blog.golang.org/feeds/posts/default",
            "category": "Core Programming Languages",
            "is_active": True,
        },
        {
            "name": "Go Weekly",
            "url": "https://golangweekly.com/rss/1jn0ck6",
            "category": "Core Programming Languages",
            "is_active": True,
        },
        # TypeScript & JavaScript Ecosystem
        {
            "name": "TypeScript Blog",
            "url": "https://devblogs.microsoft.com/typescript/feed/",
            "category": "TypeScript & JavaScript Ecosystem",
            "is_active": True,
        },
        # Web Development & Programming
        {
            "name": "Next.js Blog",
            "url": "https://nextjs.org/feed.xml",
            "category": "Web Development & Programming",
            "is_active": True,
        },
        # Official Documentation
        {
            "name": "React Blog",
            "url": "https://react.dev/rss.xml",
            "category": "Official Documentation",
            "is_active": True,
        },
        {
            "name": "Node.js Blog",
            "url": "https://nodejs.org/en/feed/blog.xml",
            "category": "Official Documentation",
            "is_active": True,
        },
        {
            "name": "MDN Web Docs Blog",
            "url": "https://developer.mozilla.org/en-US/blog/rss.xml",
            "category": "Official Documentation",
            "is_active": True,
        },
        # Official Updates
        {
            "name": "GitHub Blog",
            "url": "https://github.blog/feed/",
            "category": "Official Updates",
            "is_active": True,
        },
        # Tech Strategy & Engineering Management
        {
            "name": "The Pragmatic Engineer",
            "url": "https://blog.pragmaticengineer.com/rss/",
            "category": "Tech Strategy & Engineering Management",
            "is_active": True,
        },
        {
            "name": "Stratechery",
            "url": "https://stratechery.com/feed/",
            "category": "Tech Strategy & Engineering Management",
            "is_active": True,
        },
        # Platform Aggregators
        {
            "name": "TLDR Tech",
            "url": "https://tldr.tech/api/rss/tech",
            "category": "Platform Aggregators",
            "is_active": True,
        },
    ]

    print("Supabase client initialized successfully")
    print(f"Ready to seed {len(default_feeds)} feeds...")

    # Insert feeds with error handling
    inserted_count = 0
    skipped_count = 0

    for feed in default_feeds:
        try:
            # Attempt to insert the feed
            supabase.table("feeds").insert(feed).execute()
            inserted_count += 1
            print(f"✓ Inserted: {feed['name']}")
        except Exception as e:
            error_message = str(e).lower()

            # Handle duplicate URL error
            if "duplicate" in error_message or "unique" in error_message:
                skipped_count += 1
                print(f"⊘ Skipped (duplicate URL): {feed['name']} - {feed['url']}")
                continue

            # Handle connection errors
            elif (
                "connection" in error_message
                or "network" in error_message
                or "timeout" in error_message
            ):
                raise ConnectionError(
                    f"Error: Network error while inserting feed '{feed['name']}'\n"
                    f"Please check your internet connection and try again\n"
                    f"If the problem persists, check Supabase status at status.supabase.com\n"
                    f"Details: {e!s}"
                )

            # Re-raise other unexpected errors
            else:
                raise Exception(
                    f"Error: Unexpected error while inserting feed '{feed['name']}'\n"
                    f"Details: {e!s}"
                )

    # Print summary
    print("\n" + "=" * 50)
    print("Seeding completed!")
    print(f"Successfully inserted: {inserted_count} feeds")
    if skipped_count > 0:
        print(f"Skipped (duplicates): {skipped_count} feeds")
    print("=" * 50)


if __name__ == "__main__":
    main()
